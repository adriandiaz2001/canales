"""YouTube Data API v3: subida de Shorts con fecha de publicación (publishAt).

YouTube guarda la programación en sus servidores, así que el vídeo se sube en cuanto
entra en la cola y sale solo a su hora aunque el PC esté apagado.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from .comun import CANALES, SECRETOS, guardar_secreto, leer_secreto, registro

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]
CLIENTE = SECRETOS / "google-cliente.json"   # descargado de Google Cloud (app de escritorio)


def autorizar(canal: str) -> None:
    """Abre el navegador para que Adrián elija el canal y dé permiso. Guarda el token."""
    if not CLIENTE.exists():
        raise RuntimeError(f"Falta {CLIENTE} (mira CONFIGURAR.md, paso YouTube)")
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENTE), SCOPES)
    print(f"\nEn el navegador, elige el canal «{CANALES[canal]['nombre']}» cuando te pregunte.\n")
    creds = flow.run_local_server(port=0, prompt="consent")
    yt = build("youtube", "v3", credentials=creds, cache_discovery=False)
    yo = yt.channels().list(part="snippet", mine=True).execute()["items"][0]
    if yo["id"] != CANALES[canal]["youtube"]:
        raise RuntimeError(f"Has autorizado «{yo['snippet']['title']}» ({yo['id']}), no {CANALES[canal]['nombre']}. Repite y elige el canal correcto.")
    guardar_secreto(f"youtube-{canal}.json", __import__("json").loads(creds.to_json()))
    print(f"OK: YouTube autorizado para {yo['snippet']['title']}")


def _cliente(canal: str):
    datos = leer_secreto(f"youtube-{canal}.json")
    if not datos:
        raise RuntimeError(f"YouTube sin autorizar para {canal}: python -m publicador.autorizar youtube {canal}")
    creds = Credentials.from_authorized_user_info(datos, SCOPES)
    if not creds.valid:
        creds.refresh(Request())
        guardar_secreto(f"youtube-{canal}.json", __import__("json").loads(creds.to_json()))
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def publicar(canal: str, mp4: Path, portada: Path | None, texto: dict, fecha: datetime) -> str:
    log = registro()
    yt = _cliente(canal)
    yo = yt.channels().list(part="id", mine=True).execute()["items"][0]["id"]
    if yo != CANALES[canal]["youtube"]:
        raise RuntimeError(f"El token de {canal} apunta al canal {yo}; no publico.")

    estado = {"selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}
    if fecha > datetime.now(timezone.utc):
        estado |= {"privacyStatus": "private", "publishAt": fecha.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")}
    else:
        estado |= {"privacyStatus": "public"}

    cuerpo = {
        "snippet": {
            "title": texto["yt_titulo"][:100],
            "description": texto["yt_descripcion"],
            "tags": texto["yt_etiquetas"],
            "categoryId": "27",            # Educación
            "defaultLanguage": "es",
            "defaultAudioLanguage": "es",
        },
        "status": estado,
    }
    media = MediaFileUpload(str(mp4), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body=cuerpo, media_body=media)
    resp = None
    while resp is None:
        prog, resp = req.next_chunk()
        if prog:
            log.info("YouTube %s: %d%%", canal, int(prog.progress() * 100))
    vid = resp["id"]
    if portada:
        try:
            yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(portada), mimetype="image/png")).execute()
        except Exception as e:  # los Shorts a veces no admiten miniatura propia; no es grave
            log.warning("YouTube %s: no se pudo poner la portada (%s)", canal, e)
    return f"https://youtube.com/shorts/{vid}"
