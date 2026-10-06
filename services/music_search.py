import logging
from typing import List, Dict

import requests

from config import DEEZER_API_BASE, MAX_SEARCH_RESULTS, HTTP_TIMEOUT

logger = logging.getLogger(__name__)


class MusicSearchService:
    """Servicio para buscar música usando la API de Deezer"""

    def __init__(self):
        self.base_url = DEEZER_API_BASE
        # Reutilizar conexiones TCP para mayor velocidad
        self.session = requests.Session()

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        """Realiza un GET a la API de Deezer con manejo de errores"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        return response.json()

    def search_tracks(
        self, query: str, limit: int = MAX_SEARCH_RESULTS
    ) -> List[Dict]:
        """Buscar canciones por nombre"""
        try:
            data = self._get("/search/track", {"q": query, "limit": limit})
            return [
                {
                    "id": track["id"],
                    "title": track["title"],
                    "artist": track["artist"]["name"],
                    "album": track["album"]["title"],
                    "duration": track["duration"],
                    "preview": track.get("preview"),
                    "cover": track["album"].get("cover_medium"),
                }
                for track in data.get("data", [])
            ]
        except Exception as e:
            logger.error("Error buscando canciones: %s", e)
            return []

    def search_artists(
        self, query: str, limit: int = MAX_SEARCH_RESULTS
    ) -> List[Dict]:
        """Buscar artistas por nombre"""
        try:
            data = self._get("/search/artist", {"q": query, "limit": limit})
            return [
                {
                    "id": artist["id"],
                    "name": artist["name"],
                    "picture": artist.get("picture_medium"),
                    "nb_album": artist.get("nb_album", 0),
                    "nb_fan": artist.get("nb_fan", 0),
                }
                for artist in data.get("data", [])
            ]
        except Exception as e:
            logger.error("Error buscando artistas: %s", e)
            return []

    def search_albums(
        self, query: str, limit: int = MAX_SEARCH_RESULTS
    ) -> List[Dict]:
        """Buscar álbumes por nombre"""
        try:
            data = self._get("/search/album", {"q": query, "limit": limit})
            return [
                {
                    "id": album["id"],
                    "title": album["title"],
                    "artist": album["artist"]["name"],
                    "cover": album.get("cover_medium"),
                    "nb_tracks": album.get("nb_tracks", 0),
                }
                for album in data.get("data", [])
            ]
        except Exception as e:
            logger.error("Error buscando álbumes: %s", e)
            return []

    def get_artist_top_tracks(
        self, artist_id: int, limit: int = MAX_SEARCH_RESULTS
    ) -> List[Dict]:
        """Obtener las canciones principales de un artista"""
        try:
            data = self._get(f"/artist/{artist_id}/top", {"limit": limit})
            return [
                {
                    "id": track["id"],
                    "title": track["title"],
                    "artist": track["artist"]["name"],
                    "album": track["album"]["title"],
                    "duration": track["duration"],
                    "preview": track.get("preview"),
                    "cover": track["album"].get("cover_medium"),
                }
                for track in data.get("data", [])
            ]
        except Exception as e:
            logger.error("Error obteniendo canciones del artista: %s", e)
            return []

    def get_album_tracks(self, album_id: int) -> List[Dict]:
        """Obtener todas las canciones de un álbum (una sola llamada API)"""
        try:
            # Obtener info completa del álbum (ya incluye tracks)
            album_data = self._get(f"/album/{album_id}")
            album_title = album_data.get("title", "")
            album_cover = album_data.get("cover_medium")

            tracks_data = album_data.get("tracks", {}).get("data", [])

            return [
                {
                    "id": track["id"],
                    "title": track["title"],
                    "artist": track["artist"]["name"],
                    "album": album_title,
                    "duration": track["duration"],
                    "preview": track.get("preview"),
                    "cover": album_cover,
                }
                for track in tracks_data
            ]
        except Exception as e:
            logger.error("Error obteniendo canciones del álbum: %s", e)
            return []

    @staticmethod
    def format_duration(seconds: int) -> str:
        """Formatear duración en segundos a MM:SS"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"


# Instancia global del servicio
music_service = MusicSearchService()