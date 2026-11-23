"""Autorizaciones de una sola vez (las hace Adrián, no el programa).

  python -m publicador.autorizar youtube error404
  python -m publicador.autorizar youtube bitabit
  python -m publicador.autorizar instagram error404   (pide pegar el token del panel de Meta)
  python -m publicador.autorizar tiktok bitabit
"""
import getpass
import sys

from .comun import CANALES, cargar_env


def main() -> None:
    cargar_env()
    if len(sys.argv) != 3 or sys.argv[1] not in ("youtube", "instagram", "tiktok") or sys.argv[2] not in CANALES:
        print(__doc__)
        sys.exit(1)
    red, canal = sys.argv[1], sys.argv[2]
    if red == "youtube":
        from . import youtube
        youtube.autorizar(canal)
    elif red == "instagram":
        from . import instagram
        token = getpass.getpass(f"Pega el token de Instagram de @{CANALES[canal]['instagram']} (no se verá): ").strip()
        instagram.autorizar(canal, token)
    else:
        from . import tiktok
        tiktok.autorizar(canal)


if __name__ == "__main__":
    main()
