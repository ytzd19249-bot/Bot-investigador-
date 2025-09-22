# Bot Investigador — despliegue rápido

## Archivos incluidos
- main.py
- hotmart_api.py
- db.py
- requirements.txt
- render.yaml
- .env.example

## Variables de entorno obligatorias (Render)
- DATABASE_URL
- HOTMART_CLIENT_ID
- HOTMART_CLIENT_SECRET

Variables opcionales:
- HOTMART_API_BASE (por defecto: https://api-sec-vlc.hotmart.com)
- SCRAPE_INTERVAL_MINUTES (default 60)
- TOP_K_PRODUCTS (default 10)
- PAGES_TO_SCAN (default 3)
- AFFILIATION_AUTO_APPROVE (true/false)
- TELEGRAM_TOKEN y ADMIN_CHAT_ID (para notificaciones)
- ADMIN_TOKEN (para endpoints admin /admin/run_now, /admin/status)

## Despliegue en Render (resumen)
1. Subir todos los archivos al repo.
2. Crear un servicio tipo **Worker** en Render o usar `render.yaml`.
   - startCommand: `python main.py`
3. Agregar variables de entorno en Render (DATABASE_URL, HOTMART_*).
4. Hacer deploy.
5. Revisar logs: debe aparecer `Scheduler iniciado` y luego mensajes `Guardado producto:`.

## Probar manualmente
- Endpoint health: `GET https://TU_SERVICE.onrender.com/health`
- Forzar ciclo: `POST https://TU_SERVICE.onrender.com/admin/run_now?token=MICLAVEADMIN`

## Notas
- Ajusta los endpoints de hotmart en `hotmart_api.py` si Hotmart cambia la ruta.
- El scoring es una heurística; para mejor precisión reemplazar con GPT-R (llamada a LLM).
