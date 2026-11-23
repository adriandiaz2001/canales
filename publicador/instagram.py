"""Instagram API con inicio de sesión de Instagram: publicación de reels.

Flujo oficial: crear contenedor REELS con subida reanudable -> subir el mp4 a
rupload.facebook.com -> esperar a que el contenedor esté FINISHED -> media_publish.
El token de larga duración dura 60 días; se renueva solo cuando tiene más de 20.
"""
from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

from .comun import CANALES, env, guardar_secreto, leer_secreto, registro

def _api() -> str:
    return f"https://graph.instagram.com/{env('IG_API_VERSION', 'v23.0')}"


def autorizar(canal: str, token: str) -> None:
    """Guarda el token generado en el panel de Meta, comprobando que es de la cuenta correcta."""
    r = requests.get(f"{_api()}/me", params={"fields": "user_id,username", "access_token": token}, timeout=30)
    r.raise_for_status()
    yo = r.json()
    if yo["username"].lower() != CANALES[canal]["instagram"]:
        raise RuntimeError(f"Ese token es de @{yo['username']}, no de @{CANALES[canal]['instagram']}.")
    guardar_secreto(f"instagram-{canal}.json", {
        "access_token": token, "ig_user_id": yo["user_id"], "username": yo["username"],
        "renovado": datetime.now(timezone.utc).isoformat(),
    })
    print(f"OK: Instagram autorizado para @{yo['username']}")


def _token(canal: str) -> dict:
    s = leer_secreto(f"instagram-{canal}.json")
    if not s:
        raise RuntimeError(f"Instagram sin autorizar para {canal}: python -m publicador.autorizar instagram {canal}")
    if datetime.now(timezone.utc) - datetime.fromisoformat(s["renovado"]) > timedelta(days=20):
        r = requests.get("https://graph.instagram.com/refresh_access_token",
                         params={"grant_type": "ig_refresh_token", "access_token": s["access_token"]}, timeout=30)
        r.raise_for_status()
        s["access_token"] = r.json()["access_token"]
        s["renovado"] = datetime.now(timezone.utc).isoformat()
        guardar_secreto(f"instagram-{canal}.json", s)
        registro().info("Instagram %s: token renovado", canal)
    return s


def _ok(r: requests.Response) -> dict:
    if r.status_code >= 400:
        raise RuntimeError(f"Instagram {r.status_code}: {r.text[:500]}")
    return r.json()


def publicar(canal: str, mp4: Path, portada: Path | None, texto: dict) -> str:
    log = registro()
    s = _token(canal)
    tok, uid = s["access_token"], s["ig_user_id"]
    yo = _ok(requests.get(f"{_api()}/me", params={"fields": "username", "access_token": tok}, timeout=30))
    if yo["username"].lower() != CANALES[canal]["instagram"]:
        raise RuntimeError(f"El token de {canal} es de @{yo['username']}; no publico.")

    datos = {
        "media_type": "REELS",
        "upload_type": "resumable",
        "caption": texto["instagram"],
        "share_to_feed": "true",
        "access_token": tok,
    }
    # La portada por API solo admite una URL pública (cover_url). Si hay alojamiento configurado se usa;
    # si no, se toma un fotograma del vídeo (thumb_offset, en ms).
    base = __import__("os").environ.get("IG_PORTADAS_URL")
    if base and portada:
        datos["cover_url"] = f"{base.rstrip('/')}/{portada.name}"
    else:
        datos["thumb_offset"] = env("IG_THUMB_OFFSET_MS", "1500")

    cont = _ok(requests.post(f"{_api()}/{uid}/media", data=datos, timeout=60))
    cid = cont["id"]
    tam = mp4.stat().st_size
    with mp4.open("rb") as f:
        _ok(requests.post(cont.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{env('IG_API_VERSION', 'v23.0')}/{cid}",
                          headers={"Authorization": f"OAuth {tok}", "offset": "0", "file_size": str(tam)},
                          data=f, timeout=600))
    log.info("Instagram %s: vídeo subido (%d KB), procesando…", canal, tam // 1024)

    for _ in range(60):                       # hasta 10 minutos
        st = _ok(requests.get(f"{_api()}/{cid}", params={"fields": "status_code,status", "access_token": tok}, timeout=30))
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram rechazó el vídeo: {st}")
        time.sleep(10)
    else:
        raise RuntimeError("Instagram tardó demasiado en procesar el vídeo")

    pub = _ok(requests.post(f"{_api()}/{uid}/media_publish", data={"creation_id": cid, "access_token": tok}, timeout=60))
    link = _ok(requests.get(f"{_api()}/{pub['id']}", params={"fields": "permalink", "access_token": tok}, timeout=30))
    return link.get("permalink", f"id {pub['id']}")
