import pip_system_certs.wrapt_requests  # noqa: F401 — certificados SSL del sistema (Windows)

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env si existe
load_dotenv()

# Token del bot — SOLO desde variable de entorno
TOKEN = os.getenv("TELEGRAM_TOKEN", "")

# Directorio para descargas
DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

# API de Deezer (no requiere autenticación)
DEEZER_API_BASE = "https://api.deezer.com"

# Configuración de yt-dlp para descargas
YT_DLP_OPTIONS = {
    "format": "bestaudio/best",
    "postprocessors": [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }
    ],
    "outtmpl": str(DOWNLOADS_DIR / "%(title)s.%(ext)s"),
    "quiet": True,
    "no_warnings": True,
    "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    "js_runtimes": {"node": {}},
}

# Límite de resultados por búsqueda
MAX_SEARCH_RESULTS = 10

# Timeout para requests HTTP (segundos)
HTTP_TIMEOUT = 10