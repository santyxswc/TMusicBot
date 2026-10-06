import logging
import os
import time
import traceback
from pathlib import Path
from typing import Optional

import yt_dlp

from config import YT_DLP_OPTIONS, DOWNLOADS_DIR

logger = logging.getLogger(__name__)

# Extensiones de audio válidas
AUDIO_EXTENSIONS = {".mp3", ".m4a", ".webm", ".opus", ".ogg"}


class MusicDownloader:
    """Servicio para descargar música desde YouTube usando yt-dlp"""

    def __init__(self):
        self.download_dir = DOWNLOADS_DIR
        self.ydl_opts = YT_DLP_OPTIONS.copy()

    def download_track(
        self, track_name: str, artist_name: str
    ) -> Optional[str]:
        """
        Descargar una canción desde YouTube

        Args:
            track_name: Nombre de la canción
            artist_name: Nombre del artista

        Returns:
            Ruta del archivo descargado o None si hubo error
        """
        try:
            search_query = f"ytsearch1:{artist_name} - {track_name}"

            ydl_opts = self.ydl_opts.copy()
            safe_filename = self._sanitize_filename(
                f"{artist_name} - {track_name}"
            )
            ydl_opts["outtmpl"] = str(
                self.download_dir / f"{safe_filename}.%(ext)s"
            )

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                logger.info("Buscando: %s - %s", artist_name, track_name)

                try:
                    info = ydl.extract_info(search_query, download=True)
                except Exception as e:
                    logger.error("Error durante extract_info: %s", e)
                    return None

                if not info:
                    logger.error("No se obtuvo información del video")
                    return None

                # Verificar si tiene entries (search result)
                entries = info.get("entries", [])
                if entries and len(entries) > 0:
                    entry = entries[0]
                    if not entry:
                        logger.error("Entry vacío")
                        return None
                    logger.info(
                        "Video encontrado: %s",
                        entry.get("title", "unknown"),
                    )
                else:
                    logger.error("No se encontraron resultados de búsqueda")
                    return None

                # Buscar el archivo descargado
                return self._find_downloaded_file(safe_filename)

        except Exception as e:
            logger.error("Error general descargando canción: %s", e)
            traceback.print_exc()
            return None

    def _find_downloaded_file(self, safe_filename: str) -> Optional[str]:
        """Busca el archivo descargado en el directorio de descargas"""
        # Intento 1: nombre exacto con .mp3
        file_path = self.download_dir / f"{safe_filename}.mp3"
        if file_path.exists():
            logger.info("Archivo encontrado: %s", file_path)
            return str(file_path)

        # Intento 2: cualquier extensión de audio con el mismo nombre base
        for file in self.download_dir.glob(f"{safe_filename}.*"):
            if file.suffix in AUDIO_EXTENSIONS:
                logger.info("Archivo encontrado: %s", file)
                return str(file)

        # Intento 3: archivo reciente (último minuto)
        current_time = time.time()
        for file in self.download_dir.iterdir():
            if (
                file.is_file()
                and file.suffix in AUDIO_EXTENSIONS
                and (current_time - file.stat().st_mtime) < 60
            ):
                logger.info("Archivo reciente encontrado: %s", file)
                return str(file)

        logger.error("No se encontró el archivo descargado")
        return None

    def cleanup_file(self, file_path: str) -> bool:
        """Eliminar un archivo descargado"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("Archivo eliminado: %s", file_path)
                return True
            return False
        except Exception as e:
            logger.error("Error eliminando archivo: %s", e)
            return False

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """Sanitizar nombre de archivo para evitar caracteres inválidos"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, "_")

        if len(filename) > 200:
            filename = filename[:200]

        return filename.strip()


# Instancia global del downloader
downloader = MusicDownloader()
