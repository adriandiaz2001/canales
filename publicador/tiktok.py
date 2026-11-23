"""TikTok Content Posting API.

Dos modos (TIKTOK_MODO en .env):
  - "borrador": manda el vídeo a la bandeja de TikTok del móvil; tú solo pulsas Publicar.
               Funciona sin que TikTok audite la app.
  - "directo":  publica directamente. Hasta que TikTok audite la app, solo deja publicar
               en privado (SELF_ONLY); tras la auditoría, en público.
"""
from __future__ import annotations

import base64
import hashlib
import http.server
import secrets
import time
import urllib.parse
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from .comun import env, guardar_secreto, leer_secreto, registro

API = "https://open.tiktokapis.com/v2"
SCOPES = "user.info.basic,video.upload,video.publish"


def autorizar(canal: str) -> None:
    """OAuth con PKCE y un servidor local para recoger el código."""
    clave, secreto = env("TIKTOK_CLIENT_KEY"), env("TIKTOK_CLIENT_SECRET")
    redirect = env("TIKTOK_REDIRECT_URI", "http://localhost:8765/callback/")
    verificador = secrets.token_urlsafe(64)
    reto = base64.urlsafe_b64encode(hashlib.sha256(verificador.encode()).digest()).decode().rstrip("=")
    estado = secrets.token_urlsafe(16)
    url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
        "client_key": clave, "scope": SCOPES, "response_type": "code", "redirect_uri": redirect,
        "state": estado, "code_challenge": reto, "code_challenge_method": "S256",
    })
    recogido: dict = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            recogido.update({k: v[0] for k, v in q.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("Listo, ya puedes cerrar esta pestaña.".encode())

        def log_message(self, *a):
            pass

    puerto = urllib.parse.urlparse(redirect).port or 80
    print(f"\nInicia sesión en TikTok con la cuenta de {canal} y acepta los permisos.\n")
    webbrowser.open(url)
    with http.server.HTTPServer(("localhost", puerto), H) as srv:
        while "code" not in recogido and "error" not in recogido:
            srv.handle_request()
    if recogido.get("state") != estado or "code" not in recogido:
        raise RuntimeError(f"Autorización de TikTok fallida: {recogido}")
    r = requests.post(f"{API}/oauth/token/", data={
        "client_key": clave, "client_secret": secreto, "code": recogido["code"],
        "grant_type": "authorization_code", "redirect_uri": redirect, "code_verifier": verificador,
    }, timeout=30)
    t = _guardar(canal, r)
    info = requests.get(f"{API}/user/info/", params={"fields": "display_name"},
                        headers={"Authorization": f"Bearer {t['access_token']}"}, timeout=30).json()
    print(f"OK: TikTok autorizado para «{info.get('data', {}).get('user', {}).get('display_name', '?')}». Comprueba que es {canal}.")


def _guardar(canal: str, r: requests.Response) -> dict:
    d = r.json()
    if "access_token" not in d:
        raise RuntimeError(f"TikTok no devolvió token: {d}")
    ahora = datetime.now(timezone.utc)
    t = {"access_token": d["access_token"], "refresh_token": d["refresh_token"], "open_id": d.get("open_id"),
         "caduca": (ahora + timedelta(seconds=int(d["expires_in"]) - 300)).isoformat()}
    guardar_secreto(f"tiktok-{canal}.json", t)
    return t


def _token(canal: str) -> str:
    t = leer_secreto(f"tiktok-{canal}.json")
    if not t:
        raise RuntimeError(f"TikTok sin autorizar para {canal}: python -m publicador.autorizar tiktok {canal}")
    if datetime.now(timezone.utc) >= datetime.fromisoformat(t["caduca"]):
        r = requests.post(f"{API}/oauth/token/", data={
            "client_key": env("TIKTOK_CLIENT_KEY"), "client_secret": env("TIKTOK_CLIENT_SECRET"),
            "grant_type": "refresh_token", "refresh_token": t["refresh_token"]}, timeout=30)
        t = _guardar(canal, r)
    return t["access_token"]


def _post(ruta: str, tok: str, cuerpo: dict) -> dict:
    r = requests.post(f"{API}{ruta}", json=cuerpo, timeout=60,
                      headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8"})
    d = r.json()
    if r.status_code >= 400 or d.get("error", {}).get("code", "ok") != "ok":
        raise RuntimeError(f"TikTok {ruta}: {d.get('error', d)}")
    return d.get("data", {})


def publicar(canal: str, mp4: Path, texto: dict) -> str:
    log = registro()
    tok = _token(canal)
    modo = env("TIKTOK_MODO", "borrador")
    tam = mp4.stat().st_size
    fuente = {"source": "FILE_UPLOAD", "video_size": tam, "chunk_size": tam, "total_chunk_count": 1}

    if modo == "directo":
        info = _post("/post/publish/creator_info/query/", tok, {})
        opciones = info.get("privacy_level_options", [])
        privacidad = "PUBLIC_TO_EVERYONE" if "PUBLIC_TO_EVERYONE" in opciones else "SELF_ONLY"
        if privacidad != "PUBLIC_TO_EVERYONE":
            log.warning("TikTok %s: la app aún no está auditada; se publicará en PRIVADO", canal)
        d = _post("/post/publish/video/init/", tok, {
            "post_info": {"title": texto["tiktok"][:2200], "privacy_level": privacidad,
                          "disable_duet": False, "disable_comment": False, "disable_stitch": False,
                          "video_cover_timestamp_ms": 1500, "is_aigc": True},
            "source_info": fuente})
    else:
        d = _post("/post/publish/inbox/video/init/", tok, {"source_info": fuente})

    with mp4.open("rb") as f:
        r = requests.put(d["upload_url"], data=f, timeout=600, headers={
            "Content-Type": "video/mp4", "Content-Length": str(tam), "Content-Range": f"bytes 0-{tam - 1}/{tam}"})
    if r.status_code >= 400:
        raise RuntimeError(f"TikTok subida {r.status_code}: {r.text[:300]}")

    for _ in range(60):
        st = _post("/post/publish/status/fetch/", tok, {"publish_id": d["publish_id"]})
        s = st.get("status")
        if s in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
            if s == "SEND_TO_USER_INBOX":
                return "en tu bandeja de TikTok (falta pulsar Publicar en el móvil)"
            return "publicado" if modo != "directo" or privacidad == "PUBLIC_TO_EVERYONE" else "publicado en PRIVADO (la app aún no está auditada)"
        if s == "FAILED":
            raise RuntimeError(f"TikTok falló: {st.get('fail_reason')}")
        time.sleep(10)
    return f"enviado (publish_id {d['publish_id']}), TikTok sigue procesándolo"
