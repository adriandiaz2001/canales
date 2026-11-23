"""Dice qué está configurado y qué falta, con el siguiente paso de cada cosa.

  python -m publicador.comprobar            solo mira archivos
  python -m publicador.comprobar --online   además prueba cada token contra su API (no publica nada)
"""
from __future__ import annotations

import os
import sys

from .comun import AQUI, CANALES, SECRETOS, cargar_env, leer_secreto

OK, NO = "✔", "✘"


def linea(ok: bool, texto: str, siguiente: str = "") -> None:
    print(f"  {OK if ok else NO} {texto}" + ("" if ok or not siguiente else f"\n      → {siguiente}"))


def main() -> None:
    cargar_env()
    online = "--online" in sys.argv

    print("\nGeneral")
    linea((AQUI / ".env").exists(), "publicador\\.env", "copia .env.ejemplo como .env")
    url = os.environ.get("IG_PORTADAS_URL", "")
    linea(bool(url), f"portadas públicas para Instagram {url}", "opcional: FORMULARIOS.md, paso 0")
    for f in ("privacidad.html", "terminos.html"):
        txt = (AQUI / "web" / f).read_text(encoding="utf-8")
        linea("CORREO_DE_CONTACTO" not in txt, f"web/{f} con correo de contacto", "sustituye CORREO_DE_CONTACTO")

    print("\nYouTube")
    linea((SECRETOS / "google-cliente.json").exists(), "secretos\\google-cliente.json", "CONFIGURAR.md, YouTube pasos 1-4")
    for c in CANALES:
        tiene = leer_secreto(f"youtube-{c}.json") is not None
        linea(tiene, f"autorizado {CANALES[c]['nombre']}", f"python -m publicador.autorizar youtube {c}")
        if tiene and online:
            try:
                from . import youtube
                yt = youtube._cliente(c)
                yo = yt.channels().list(part="snippet", mine=True).execute()["items"][0]
                linea(yo["id"] == CANALES[c]["youtube"], f"    token válido → {yo['snippet']['title']}")
            except Exception as e:
                linea(False, f"    token: {e}", f"python -m publicador.autorizar youtube {c}")

    print("\nInstagram")
    for c in CANALES:
        s = leer_secreto(f"instagram-{c}.json")
        linea(s is not None, f"autorizado @{CANALES[c]['instagram']}", f"python -m publicador.autorizar instagram {c}")
        if s and online:
            try:
                from . import instagram
                import requests
                t = instagram._token(c)
                yo = requests.get(f"{instagram._api()}/me", params={"fields": "username", "access_token": t["access_token"]}, timeout=30).json()
                linea(yo.get("username", "").lower() == CANALES[c]["instagram"], f"    token válido → @{yo.get('username', yo)}")
            except Exception as e:
                linea(False, f"    token: {e}", f"python -m publicador.autorizar instagram {c}")

    print("\nTikTok")
    claves = bool(os.environ.get("TIKTOK_CLIENT_KEY")) and bool(os.environ.get("TIKTOK_CLIENT_SECRET"))
    linea(claves, "TIKTOK_CLIENT_KEY y TIKTOK_CLIENT_SECRET en .env", "CONFIGURAR.md, TikTok pasos 1-5")
    print(f"    modo: {os.environ.get('TIKTOK_MODO', 'borrador')}")
    for c in CANALES:
        s = leer_secreto(f"tiktok-{c}.json")
        linea(s is not None, f"autorizado {CANALES[c]['nombre']}", f"python -m publicador.autorizar tiktok {c}")
        if s and online:
            try:
                from . import tiktok
                import requests
                tok = tiktok._token(c)
                d = requests.get(f"{tiktok.API}/user/info/", params={"fields": "display_name"},
                                 headers={"Authorization": f"Bearer {tok}"}, timeout=30).json()
                linea("data" in d, f"    token válido → {d.get('data', {}).get('user', {}).get('display_name', d)}")
            except Exception as e:
                linea(False, f"    token: {e}", f"python -m publicador.autorizar tiktok {c}")

    print("\nTarea programada")
    try:
        import subprocess
        r = subprocess.run(["schtasks", "/Query", "/TN", "Publicador canales"], capture_output=True, text=True)
        linea(r.returncode == 0, "«Publicador canales» instalada", "powershell -ExecutionPolicy Bypass -File publicador\\instalar_tarea.ps1")
    except Exception:
        linea(False, "no se pudo consultar el Programador de tareas")
    print()


if __name__ == "__main__":
    main()
