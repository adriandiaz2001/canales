# Publicador por API: configuración

El publicador sube los vídeos por las **API oficiales** de cada red, que sí están permitidas. No usa el navegador, que es lo que hizo saltar la alarma de Instagram.

Una vez configurado, para publicar un tema solo hay que meterlo en la cola:

```powershell
cd C:\Proyectos\canal-faceless
python -m publicador.publicar --programar 03 2026-11-22     # Bit a Bit 13:30 · Error 404 19:00
python -m publicador.publicar --estado                      # ver la cola
python -m publicador.publicar --seco                        # qué publicaría ahora, sin publicar
```

La tarea de Windows (`instalar_tarea.ps1`) revisa la cola cada 10 minutos y publica lo que toca:

| Red | Cómo publica | ¿Hace falta el PC encendido a la hora? |
|---|---|---|
| YouTube | Sube el vídeo en cuanto entra en la cola, con fecha de publicación | No, YouTube lo publica solo |
| Instagram | Publica a su hora | Sí (o en suspensión: la tarea lo despierta) |
| TikTok | Lo publica o lo deja en tu bandeja a su hora | Sí (o en suspensión) |

Si el PC estuvo apagado más de 6 h desde la hora prevista, no publica tarde: marca la publicación como `caducada` y hay que volver a programarla.

Lo que sigue lo tienes que hacer tú: cada paso crea una cuenta de desarrollador, pide contraseña o acepta condiciones.

**Antes de instalar nada:** copia `publicador\.env.ejemplo` como `publicador\.env`. Las claves y tokens se guardan en `publicador\.env` y `publicador\secretos\`. Esos dos sitios no se comparten con nadie.

---

## 1. YouTube (≈15 min + espera de auditoría)

1. Entra en <https://console.cloud.google.com> con tu Gmail y crea un proyecto: «Publicador canales».
2. **APIs y servicios → Biblioteca →** «YouTube Data API v3» **→ Habilitar.**
3. **Google Auth Platform / Pantalla de consentimiento:**
   - Tipo **Externo**.
   - Nombre «Publicador canales» y tu correo.
   - En **Público**, pulsa **Publicar app** («En producción»). Si la dejas en «Prueba», el permiso caduca cada 7 días. Sin verificar funciona igual: Google te enseñará un aviso al autorizar.
4. **Clientes → Crear cliente → Aplicación de escritorio.**
   - Descarga el JSON.
   - Guárdalo como `C:\Proyectos\canal-faceless\publicador\secretos\google-cliente.json`.
5. Autoriza cada canal. Se abre el navegador; elige la cuenta de marca del canal correcto:
   ```powershell
   cd C:\Proyectos\canal-faceless
   python -m publicador.autorizar youtube error404
   python -m publicador.autorizar youtube bitabit
   ```
   Si sale «Google no ha verificado esta aplicación»: **Configuración avanzada → Ir a Publicador canales**. El programa comprueba el ID del canal y se niega si eliges el que no es.
6. ⚠️ **Auditoría.** YouTube deja **en privado** todo lo que suben los proyectos nuevos de la API hasta que pasan su auditoría.
   - Pídela en el formulario «YouTube API Services – Audit and Quota Extension».
   - Uso: «subir los vídeos de mis propios dos canales».
   - Hasta que la aprueben, programa YouTube a mano en YouTube Studio y quita YouTube de la cola: `--redes instagram,tiktok`.

## 2. Instagram (≈20 min)

Espera a tener **las dos cuentas recuperadas y estables unos días** antes de conectarlas.

1. Entra en <https://developers.facebook.com>.
   - Si no lo has hecho nunca, date de alta como desarrollador.
   - Recomendado: mueve antes las dos cuentas a un Centro de cuentas separado del personal.
2. **Crear app.**
   - Caso de uso: **«Gestionar mensajes y contenido en Instagram»** (Instagram API).
   - Tipo **Negocio**.
3. En el caso de uso, entra en **«Configuración de la API con inicio de sesión de Instagram»**.
   - Comprueba que estén los permisos `instagram_business_basic` e `instagram_business_content_publish`.
4. **Generar tokens de acceso → Añadir cuenta:**
   - Entra con **error404neuronas** y acepta. Repite con **bitabit.explica**.
   - Si te pide que la cuenta sea **probador de Instagram**:
     - **Roles de la app → Roles → Probadores de Instagram**: invita a la cuenta.
     - Acepta la invitación en instagram.com → Configuración → Apps y sitios web.
5. Pulsa **Generar token** en cada cuenta, cópialo y guárdalo:
   ```powershell
   python -m publicador.autorizar instagram error404
   python -m publicador.autorizar instagram bitabit
   ```
   Te pide pegar el token (no se ve al pegarlo). Comprueba que es de la cuenta correcta. El programa lo renueva solo antes de que caduque a los 60 días.

La app puede quedarse en **modo desarrollo**: para publicar en tus propias cuentas no hace falta revisión de Meta.

**Dos límites de la API de Instagram:**
- **Portada:** solo acepta una URL pública. Sin ella, la portada es el fotograma del segundo 1,5 (`IG_THUMB_OFFSET_MS`). Si quieres la portada png, te monto una carpeta pública y la pones en `IG_PORTADAS_URL`.
- **Etiqueta de IA:** la API no tiene el interruptor «Añadir etiqueta de IA». Instagram solo la exige para vídeos *realistas*, y los nuestros son dibujos low-poly. Si aun así quieres dejarlo claro, añade una línea «Vídeo hecho con IA» al texto.

## 3. TikTok (≈30 min + revisión de TikTok)

1. Entra en <https://developers.tiktok.com>, regístrate y ve a **Manage apps → Connect an app**.
2. Rellena la app:
   - Nombre, icono y descripción.
   - **Platform: Desktop.**
   - TikTok pide la URL de unos **términos y una política de privacidad**. Pídemelos y te preparo las dos páginas.
3. **Products:**
   - Añade **Login Kit**. Redirect URI: `http://localhost:8765/callback/`.
   - Añade **Content Posting API**: activa *Upload* y, si quieres publicación directa, *Direct Post*.
   - **Scopes:** `user.info.basic`, `video.upload`, `video.publish`.
4. **Sandbox:** añade tus dos cuentas de TikTok como *target users* para probar ya. Para producción, envía la app a revisión.
5. Copia **Client key** y **Client secret** a `publicador\.env`.
6. Autoriza cada cuenta. Se abre el navegador; si está con la otra cuenta, cierra sesión antes:
   ```powershell
   python -m publicador.autorizar tiktok error404
   python -m publicador.autorizar tiktok bitabit
   ```

Hay dos modos, que se eligen con `TIKTOK_MODO` en `.env`:
- `borrador` (recomendado para empezar): el vídeo llega a la bandeja de tu app de TikTok y pulsas Publicar. Así eliges el sonido y la etiqueta de IA desde el móvil.
- `directo`: publica solo con «contenido generado por IA» marcado. Mientras TikTok no audite la app, solo deja publicar **en privado**. Tras la auditoría, en público.

## 4. Activar la publicación automática

Cuando tengas al menos una red autorizada:

```powershell
python -m publicador.publicar --seco
powershell -ExecutionPolicy Bypass -File C:\Proyectos\canal-faceless\publicador\instalar_tarea.ps1
```

Revisa qué ha pasado en `publicador\registro.log` o con `--estado`.
