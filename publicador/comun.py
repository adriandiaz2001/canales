"""Utilidades compartidas del publicador: rutas, configuración, secretos, registro y textos."""
from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent          # C:\Proyectos\canal-faceless
AQUI = Path(__file__).resolve().parent                 # ...\publicador
SECRETOS = AQUI / "secretos"
VIDEOS = RAIZ / "Videos"

# Canales: clave interna -> datos que usamos para comprobar que publicamos en la cuenta correcta.
CANALES = {
    "error404": {
        "nombre": "Error 404: Neuronas",
        "instagram": "error404neuronas",
        "youtube": "UCpWG-wIADicBL_dxe4Hco3w",
        "carpeta": "Error404",
        "prefijo": "e",
        "prefijos": ["e", "f"],  # f = serie #FermínLiándola
    },
    "bitabit": {
        "nombre": "Bit a Bit",
        "instagram": "bitabit.explica",
        "youtube": "UCSBrGP8z9bPV_8Wj4xAHkRw",
        "carpeta": "BitABit",
        "prefijo": "b",
    },
}


def cargar_env() -> None:
    """Lee publicador/.env (CLAVE=valor) sin depender de python-dotenv."""
    import sys
    for flujo in (sys.stdout, sys.stderr):   # la consola de Windows no sabe pintar emojis
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace")
    f = AQUI / ".env"
    if not f.exists():
        return
    for linea in f.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        k, v = linea.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def env(clave: str, defecto: str | None = None) -> str:
    v = os.environ.get(clave, defecto)
    if v is None or v == "":
        raise RuntimeError(f"Falta {clave} en publicador/.env (mira CONFIGURAR.md)")
    return v


def leer_secreto(nombre: str) -> dict | None:
    f = SECRETOS / nombre
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def guardar_secreto(nombre: str, datos: dict) -> None:
    SECRETOS.mkdir(exist_ok=True)
    (SECRETOS / nombre).write_text(json.dumps(datos, indent=2, ensure_ascii=False), encoding="utf-8")


def registro() -> logging.Logger:
    log = logging.getLogger("publicador")
    if not log.handlers:
        log.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        fh = logging.FileHandler(AQUI / "registro.log", encoding="utf-8")
        fh.setFormatter(fmt)
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        log.addHandler(fh)
        log.addHandler(sh)
    return log


# ---------------------------------------------------------------- vídeos y textos
def rutas_video(stem: str) -> tuple[Path, Path | None]:
    """'b03-ctrl-alt-supr' -> (mp4, png de portada o None)."""
    canal = canal_de(stem)
    carpeta = VIDEOS / CANALES[canal]["carpeta"]
    mp4 = carpeta / f"{stem}.mp4"
    if not mp4.exists():
        raise FileNotFoundError(mp4)
    png = carpeta / "Portadas" / f"{stem}.png"
    return mp4, (png if png.exists() else None)


def canal_de(stem: str) -> str:
    for clave, c in CANALES.items():
        if any(stem.startswith(p) for p in c.get("prefijos", [c["prefijo"]])) and stem[1:3].isdigit():
            return clave
    raise ValueError(f"No sé de qué canal es {stem}")


_CAMPO = re.compile(r"^\*\*(TikTok|Instagram|YouTube)[^*]*\*\*\s*(.*)$")
_SECCION = re.compile(r"^#{2,3}\s.*`([^`]+)\.mp4`")


def textos() -> dict[str, dict]:
    """Lee Videos/textos-*.md y devuelve {stem: {tiktok, instagram, yt_titulo, yt_descripcion, yt_etiquetas}}."""
    salida: dict[str, dict] = {}
    for md in sorted(VIDEOS.glob("textos-*.md")):
        stem, campo, buf = None, None, {}

        def cerrar():
            if stem and campo:
                buf[campo] = "\n".join(buf.get(campo + "_l", [])).strip()

        for linea in md.read_text(encoding="utf-8").splitlines():
            m = _SECCION.match(linea)
            if m or linea.startswith("## ") or linea.strip() == "---":
                cerrar()
                if stem:
                    salida[stem] = _limpiar(buf)
                stem, campo, buf = (m.group(1) if m else None), None, {}
                continue
            m = _CAMPO.match(linea)
            if m and stem:
                cerrar()
                campo = m.group(1).lower()
                buf[campo + "_l"] = [m.group(2)] if m.group(2) else []
                continue
            if stem and campo:
                buf[campo + "_l"].append(linea)
        cerrar()
        if stem:
            salida[stem] = _limpiar(buf)
    return salida


def _limpiar(buf: dict) -> dict:
    yt = buf.get("youtube", "")
    titulo = re.search(r"^Título:\s*(.+)$", yt, re.M)
    etiquetas = re.search(r"^Etiquetas:\s*(.+)$", yt, re.M)
    desc = re.search(r"^Descripción:\s*(.+?)(?=^Etiquetas:|\Z)", yt, re.M | re.S)
    return {
        "tiktok": buf.get("tiktok", ""),
        "instagram": buf.get("instagram", ""),
        "yt_titulo": titulo.group(1).strip() if titulo else "",
        "yt_descripcion": desc.group(1).strip() if desc else "",
        "yt_etiquetas": [e.strip() for e in etiquetas.group(1).split(",")] if etiquetas else [],
    }
