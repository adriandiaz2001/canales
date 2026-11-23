# Textos para copiar y pegar en los formularios

Correos de contacto: **error404neuronas@gmail.com** (Error 404: Neuronas) y **bitabitexplica@gmail.com** (Bit a Bit). Ya están puestos en `web/privacidad.html` y `web/terminos.html`. Cuando subas la web, `TU_USUARIO` será tu usuario de GitHub.

---

## 0. Publicar la web pública (GitHub Pages, gratis, ≈5 min)

La web sirve para tres cosas:
- dar a TikTok las URL de privacidad y de términos;
- dar a TikTok y Meta el icono de la app;
- poner la portada png en los reels de Instagram.

Pasos:
1. En <https://github.com/new> crea un repositorio **público** llamado `canales`.
2. **Add file → Upload files**: arrastra **todo el contenido** de `C:\Proyectos\canal-faceless\publicador\web\`, con la carpeta `portadas`. Pulsa **Commit changes**.
3. Ve a **Settings → Pages**. En Source, elige **Deploy from a branch**, rama `main`, carpeta `/ (root)`, y pulsa **Save**.
4. En un par de minutos estará en `https://TU_USUARIO.github.io/canales/`.
5. En `publicador\.env` pon `IG_PORTADAS_URL=https://TU_USUARIO.github.io/canales/portadas`.

Cada vez que haya portadas nuevas, súbelas a `portadas/` del repositorio. Si me das acceso, lo hago yo.

URLs que pedirán los formularios:
- Privacidad: `https://TU_USUARIO.github.io/canales/privacidad.html`
- Términos: `https://TU_USUARIO.github.io/canales/terminos.html`
- Web: `https://TU_USUARIO.github.io/canales/`
- Icono (1024×1024): `C:\Proyectos\canal-faceless\publicador\web\icono.png`

---

## 1. Google Cloud / YouTube

**Pantalla de consentimiento**
- Nombre de la app: `Publicador canales`
- Correo de asistencia: tu Gmail
- Página principal, privacidad y términos: las URL de arriba

**Formulario de auditoría** («YouTube API Services – Audit and Quota Extension Form»)
- Uso de la API: *Upload*.
- Descripción (en inglés):

> Publicador canales is a private desktop tool used only by me to upload my own original short educational videos (computing history) to my own two YouTube channels, "Error 404: Neuronas" (UCpWG-wIADicBL_dxe4Hco3w) and "Bit a Bit" (UCSBrGP8z9bPV_8Wj4xAHkRw). It calls videos.insert (scheduled with status.publishAt and status.containsSyntheticMedia=true) and thumbnails.set. It has no other users, does not access any other channel, and stores OAuth tokens only on my computer. Expected volume: 2 uploads per day, well within the default quota of 10,000 units.

- ¿La app la usan otros? **No, solo el propietario.**
- Usuarios esperados: **1**

---

## 2. Meta for Developers / Instagram

- Nombre de la app: `Publicador canales`
- Correo de contacto: `error404neuronas@gmail.com` (la app es una sola para los dos canales; basta un correo)
- Caso de uso: **Gestionar mensajes y contenido en Instagram**
- Privacidad: URL de arriba (Configuración de la app → Básica)
- Icono: `icono.png`

Para tus propias cuentas basta con el modo desarrollo; no hace falta revisión.

---

## 3. TikTok for Developers

| Campo | Valor |
|---|---|
| App name | `Publicador canales` |
| Category | Education (o Entertainment) |
| Platform | Desktop |
| Icon | `icono.png` |
| Terms of Service URL | `https://TU_USUARIO.github.io/canales/terminos.html` |
| Privacy Policy URL | `https://TU_USUARIO.github.io/canales/privacidad.html` |
| Login Kit → Redirect URI | `http://localhost:8765/callback/` |
| Content Posting API | Upload ✔ · Direct Post ✔ |
| Scopes | `user.info.basic`, `video.upload`, `video.publish` |

**Description**:

> Personal desktop tool that uploads my own original short educational videos about computing history to my own two TikTok accounts ("Error 404: Neuronas" and "Bit a Bit"). Videos are made with AI tools and are disclosed as AI-generated content.

**Explanation for review** (para cada producto y scope):

> This app is used only by the owner of the two accounts to publish their own original videos. Login Kit (user.info.basic) is used to confirm which of my two accounts is connected. video.upload sends finished videos to my TikTok inbox as drafts; video.publish posts them directly at a scheduled time with is_aigc=true. No data from other users is accessed or stored. Tokens are kept only on my computer.

TikTok suele pedir un **vídeo de demostración** que enseñe el flujo de la app. Cuando esté en Sandbox y funcione, grabamos la pantalla mientras ejecutas `python -m publicador.autorizar tiktok bitabit` y una publicación de prueba.
