# Plan para dejar las subidas automáticas (solo Error 404)

Bit a Bit está en pausa, así que solo hay que conectar **una cuenta por red**. Los detalles de cada paso están en `CONFIGURAR.md` y los textos para copiar y pegar en `FORMULARIOS.md`.

## Lo que hace cada parte

| Quién | Qué |
|---|---|
| **Claude** | Hace el vídeo, la portada y los textos, y lo deja en la cola con `--programar fNN AAAA-MM-DD`. |
| **El PC** | Una tarea de Windows mira la cola cada 10 minutos y publica a las 19:00 por las API oficiales. El PC tiene que estar encendido o en suspensión a esa hora. |
| **Tú** | Una sola vez: crear las apps y autorizar las cuentas. Después, solo revisar. |

## Qué queda automático en cada red

| Red | Al principio | Cuando la red apruebe la app |
|---|---|---|
| Instagram | **Automático y público desde el primer día** (modo desarrollo; vale para tu propia cuenta) | — |
| YouTube | Se sube y se programa solo, pero **en privado** hasta que Google audite la app. Tú cambias a público en Studio (1 clic). | Automático y público |
| TikTok | Llega a la **bandeja de borradores** del móvil; tú pulsas Publicar. | Automático y público |

## Pasos, en orden (≈ 1 h en total, se puede repartir)

1. **Web pública en GitHub Pages** (10 min). `FORMULARIOS.md` › 0. Pásame la URL.
2. **Instagram** (20 min). Es lo que más rinde y funciona al momento.
   - Crear la app en Meta for Developers (`CONFIGURAR.md` › Instagram).
   - `python -m publicador.autorizar instagram error404` y pegar el token cuando lo pida.
3. **YouTube** (20 min + espera de la auditoría).
   - Proyecto en Google Cloud, pantalla de consentimiento, credenciales de escritorio → `secretos/google-cliente.json`.
   - `python -m publicador.autorizar youtube error404`.
   - Enviar el formulario de auditoría (texto en `FORMULARIOS.md`). Tarda de días a semanas.
4. **TikTok** (15 min + revisión).
   - App en TikTok for Developers, `TIKTOK_MODO=borrador` en `.env`.
   - `python -m publicador.autorizar tiktok error404`.
5. **Tarea de Windows** (2 min): clic derecho en `instalar_tarea.ps1` → *Ejecutar con PowerShell*.
6. **Prueba**: `python -m publicador.comprobar --online` y `python -m publicador.publicar --seco`.

## Reglas para no repetir el susto de Instagram
- Nada de navegador automático: solo las API oficiales.
- Como mucho, 1 publicación al día por red y a la misma hora.
- Las 2 primeras semanas, mira el resultado en el móvil después de cada publicación.
