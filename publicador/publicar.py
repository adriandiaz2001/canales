"""Cola de publicación.

  python -m publicador.publicar                    publica lo que toca (lo lanza la tarea programada)
  python -m publicador.publicar --seco             dice qué publicaría y comprueba vídeos y textos, sin publicar
  python -m publicador.publicar --estado           lista la cola
  python -m publicador.publicar --programar f01 2026-11-24
        añade el capítulo 1 de #FermínLiándola (f01-*.mp4) a la cola de Error 404 a las 19:00
        (hora de Madrid) en YouTube, Instagram y TikTok. Con un número (03) busca e03/b03.
        Bit a Bit está en pausa: solo entra con --canales error404,bitabit.
        Cambia las horas con --hora-b 13:30 --hora-e 19:00 y las redes con --redes youtube,instagram
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from .comun import AQUI, CANALES, VIDEOS, cargar_env, registro, rutas_video, textos

COLA = AQUI / "cola.json"
CERROJO = AQUI / "cola.lock"
MADRID = ZoneInfo("Europe/Madrid")
REDES = ("youtube", "instagram", "tiktok")
MARGEN_RETRASO = timedelta(hours=6)   # si el PC estuvo apagado más de esto, no publica tarde: marca "caducada"


def leer_cola() -> list[dict]:
    return json.loads(COLA.read_text(encoding="utf-8")) if COLA.exists() else []


def guardar_cola(cola: list[dict]) -> None:
    COLA.write_text(json.dumps(cola, indent=2, ensure_ascii=False), encoding="utf-8")


def toca(item: dict, ahora: datetime) -> bool:
    if item["estado"] != "pendiente" or not item.get("aprobado"):
        return False
    # YouTube se sube en cuanto entra en la cola: él mismo lo publica a su hora (publishAt).
    return item["red"] == "youtube" or ahora >= datetime.fromisoformat(item["fecha"])


def publicar_item(item: dict, txt: dict) -> str:
    stem, canal, red = item["video"], item["canal"], item["red"]
    mp4, portada = rutas_video(stem)
    t = txt[stem]
    if red == "youtube":
        from . import youtube
        return youtube.publicar(canal, mp4, portada, t, datetime.fromisoformat(item["fecha"]))
    if red == "instagram":
        from . import instagram
        return instagram.publicar(canal, mp4, portada, t)
    from . import tiktok
    return tiktok.publicar(canal, mp4, t)


def comprobar(item: dict, txt: dict) -> list[str]:
    fallos = []
    try:
        rutas_video(item["video"])
    except Exception as e:
        fallos.append(f"vídeo: {e}")
    t = txt.get(item["video"])
    if not t:
        fallos.append("no hay textos en Videos/textos-*.md")
    else:
        campo = {"youtube": "yt_titulo", "instagram": "instagram", "tiktok": "tiktok"}[item["red"]]
        if not t[campo]:
            fallos.append(f"texto vacío para {item['red']}")
    return fallos


def ejecutar(seco: bool) -> None:
    log = registro()
    cola, txt = leer_cola(), textos()
    ahora = datetime.now(timezone.utc)
    cambios = False
    for item in cola:
        if item["estado"] == "pendiente" and item["red"] != "youtube" and ahora - datetime.fromisoformat(item["fecha"]) > MARGEN_RETRASO:
            item["estado"], item["resultado"] = "caducada", "el PC no estaba encendido a su hora; vuelve a programarla"
            log.warning("%s caducada", item["id"])
            cambios = True
            continue
        if not toca(item, ahora):
            continue
        fallos = comprobar(item, txt)
        if seco:
            print(f"[seco] publicaría {item['id']} ({item['red']}, {item['canal']}) {'OK' if not fallos else fallos}")
            t = txt.get(item["video"], {})
            print("        texto:", (t.get("yt_titulo") if item["red"] == "youtube" else t.get(item["red"], ""))[:90].replace("\n", " / "))
            continue
        if fallos:
            item["estado"], item["resultado"] = "error", "; ".join(fallos)
            log.error("%s: %s", item["id"], item["resultado"])
            cambios = True
            continue
        try:
            log.info("Publicando %s…", item["id"])
            item["resultado"] = publicar_item(item, txt)
            item["estado"] = "hecho"
            item["publicado"] = datetime.now(timezone.utc).isoformat()
            log.info("%s -> %s", item["id"], item["resultado"])
        except Exception as e:
            item["intentos"] = item.get("intentos", 0) + 1
            item["resultado"] = str(e)[:500]
            if item["intentos"] >= 3:
                item["estado"] = "error"
            log.exception("%s falló (intento %d)", item["id"], item["intentos"])
        cambios = True
        guardar_cola(cola)   # guarda tras cada publicación por si se corta a mitad
    if cambios and not seco:
        guardar_cola(cola)


def programar(tema: str, dia: str, hora_b: str, hora_e: str, redes: list[str], canales: list[str]) -> None:
    cola, txt = leer_cola(), textos()
    ids = {i["id"] for i in cola}
    nuevos = 0
    for canal, hora in (("bitabit", hora_b), ("error404", hora_e)):
        if canal not in canales:
            continue
        c = CANALES[canal]
        patron = f"{tema}-*.mp4" if tema[0].isalpha() else f"{c['prefijo']}{tema}-*.mp4"
        stems = sorted(p.stem for p in (VIDEOS / c["carpeta"]).glob(patron))
        if not stems:
            raise SystemExit(f"No encuentro el vídeo {patron} de {c['nombre']}")
        stem = stems[0]
        fecha = datetime.fromisoformat(f"{dia}T{hora}").replace(tzinfo=MADRID)
        for red in redes:
            item = {"id": f"{stem}-{red}", "canal": canal, "red": red, "video": stem,
                    "fecha": fecha.isoformat(), "aprobado": True, "estado": "pendiente", "resultado": None}
            if item["id"] in ids:
                print(f"Ya estaba en la cola: {item['id']}")
                continue
            fallos = comprobar(item, txt)
            if fallos:
                raise SystemExit(f"{item['id']}: {fallos}")
            cola.append(item)
            nuevos += 1
            print(f"Añadido {item['id']} para {fecha:%d/%m %H:%M}")
    guardar_cola(cola)
    print(f"{nuevos} publicaciones añadidas.")


def estado() -> None:
    for i in leer_cola():
        f = datetime.fromisoformat(i["fecha"]).astimezone(MADRID)
        print(f"{f:%d/%m %H:%M}  {i['estado']:<10} {i['id']:<32} {i.get('resultado') or ''}")


def main() -> None:
    cargar_env()
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--seco", action="store_true")
    p.add_argument("--estado", action="store_true")
    p.add_argument("--programar", nargs=2, metavar=("TEMA", "DIA"))
    p.add_argument("--hora-b", default="13:30")
    p.add_argument("--hora-e", default="19:00")
    p.add_argument("--redes", default=",".join(REDES))
    p.add_argument("--canales", default="error404", help="Bit a Bit en pausa desde el 23-nov-2026")
    a = p.parse_args()
    if a.estado:
        return estado()
    if a.programar:
        return programar(a.programar[0].zfill(2), a.programar[1], a.hora_b, a.hora_e, [r for r in a.redes.split(",") if r], a.canales.split(","))

    # Cerrojo para que dos ejecuciones de la tarea no publiquen lo mismo dos veces.
    if CERROJO.exists() and time.time() - CERROJO.stat().st_mtime > 3600:
        CERROJO.unlink()
    try:
        fd = os.open(CERROJO, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        registro().info("Ya hay otra ejecución en marcha; salgo.")
        return
    try:
        ejecutar(a.seco)
    finally:
        os.close(fd)
        CERROJO.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
