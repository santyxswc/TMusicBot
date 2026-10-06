import asyncio
import logging
from collections import OrderedDict
from uuid import uuid4

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultArticle,
    InputTextMessageContent,
    CallbackQuery,
)
from telegram.ext import ContextTypes

from services.music_search import music_service
from services.downloader import downloader

logger = logging.getLogger(__name__)

# Cache con límite para evitar memory leaks
# Diccionario: uuid -> {title, artist}
MAX_CACHE_SIZE = 500


class TrackCache:
    """Cache LRU simple para info de tracks (evita memory leak)"""

    def __init__(self, maxsize: int = MAX_CACHE_SIZE):
        self._cache: OrderedDict = OrderedDict()
        self._maxsize = maxsize

    def set(self, key: str, value: dict) -> None:
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = value
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

    def get(self, key: str) -> dict | None:
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None


track_cache = TrackCache()


async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja las búsquedas en línea con soporte para categorías"""
    query = update.inline_query.query

    if not query or len(query) < 2:
        return

    try:
        results = []

        # 1. Búsqueda de Artistas
        if query.startswith("artist: "):
            clean_q = query.removeprefix("artist: ")
            if len(clean_q) < 2:
                return

            artists = music_service.search_artists(clean_q)
            for artist in artists[:10]:
                content = InputTextMessageContent(
                    f"/view_artist {artist['id']} {artist['name']}"
                )
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid4()),
                        title=f"👤 {artist['name']}",
                        description=f"Fans: {artist['nb_fan']}",
                        input_message_content=content,
                        thumbnail_url=artist["picture"],
                    )
                )

        # 2. Búsqueda de Álbumes
        elif query.startswith("album: "):
            clean_q = query.removeprefix("album: ")
            if len(clean_q) < 2:
                return

            albums = music_service.search_albums(clean_q)
            for album in albums[:10]:
                content = InputTextMessageContent(
                    f"/view_album {album['id']} {album['title']}"
                )
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid4()),
                        title=f"💿 {album['title']}",
                        description=f"Artista: {album['artist']}",
                        input_message_content=content,
                        thumbnail_url=album["cover"],
                    )
                )

        # 3. Búsqueda de Canciones (Default)
        else:
            tracks = music_service.search_tracks(query)
            for track in tracks[:15]:
                content = InputTextMessageContent(
                    f"/dl_track {track['title']} - {track['artist']}"
                )
                results.append(
                    InlineQueryResultArticle(
                        id=str(uuid4()),
                        title=f"🎵 {track['title']}",
                        description=f"👤 {track['artist']}\n💿 {track['album']}",
                        input_message_content=content,
                        thumbnail_url=track["cover"],
                    )
                )

        await update.inline_query.answer(results, cache_time=1)

    except Exception as e:
        logger.error("Error en inline_query: %s", e)


async def handle_inline_result(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Maneja la selección directa de canción (/dl_track)"""
    message_text = update.message.text
    if not message_text.startswith("/dl_track"):
        return

    query_string = message_text.removeprefix("/dl_track").strip()
    if not query_string:
        return

    if " - " in query_string:
        track_name, artist_name = query_string.split(" - ", 1)
    else:
        track_name, artist_name = query_string, ""

    await _start_download(update, context, track_name, artist_name)


async def handle_view_artist(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Maneja la selección de un artista (/view_artist ID Name)"""
    try:
        parts = update.message.text.split(" ", 2)
        if len(parts) < 3:
            await update.message.reply_text(
                "❌ Formato inválido. Usa la búsqueda inline para seleccionar un artista."
            )
            return

        artist_id = parts[1]
        artist_name = parts[2]

        status_msg = await update.message.reply_text(
            f"⏳ Obteniendo canciones de *{artist_name}*...",
            parse_mode="Markdown",
        )

        tracks = music_service.get_artist_top_tracks(artist_id, limit=10)

        if not tracks:
            await status_msg.edit_text(
                f"❌ No se encontraron canciones de *{artist_name}*.",
                parse_mode="Markdown",
            )
            return

        keyboard = []
        for track in tracks:
            track_uuid = str(uuid4())[:8]
            track_cache.set(
                track_uuid,
                {"title": track["title"], "artist": track["artist"]},
            )

            duration = music_service.format_duration(track["duration"])
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"🎵 {track['title']} ({duration})",
                        callback_data=f"dl_uuid_{track_uuid}",
                    )
                ]
            )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔙 Volver al Menú",
                    switch_inline_query_current_chat="",
                )
            ]
        )

        await status_msg.edit_text(
            f"👤 *Top Canciones de {artist_name}:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error("Error view_artist: %s", e)
        await update.message.reply_text(
            "❌ Error al obtener canciones del artista. Intenta de nuevo."
        )


async def handle_view_album(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Maneja la selección de un álbum (/view_album ID Title)"""
    try:
        parts = update.message.text.split(" ", 2)
        if len(parts) < 3:
            await update.message.reply_text(
                "❌ Formato inválido. Usa la búsqueda inline para seleccionar un álbum."
            )
            return

        album_id = parts[1]
        album_title = parts[2]

        status_msg = await update.message.reply_text(
            f"⏳ Obteniendo canciones del álbum *{album_title}*...",
            parse_mode="Markdown",
        )

        tracks = music_service.get_album_tracks(album_id)
        tracks = tracks[:15]  # Limitar para no saturar

        if not tracks:
            await status_msg.edit_text(
                f"❌ No se encontraron canciones en el álbum *{album_title}*.",
                parse_mode="Markdown",
            )
            return

        keyboard = []
        for track in tracks:
            track_uuid = str(uuid4())[:8]
            track_cache.set(
                track_uuid,
                {"title": track["title"], "artist": track["artist"]},
            )

            duration = music_service.format_duration(track["duration"])
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"🎵 {track['title']} ({duration})",
                        callback_data=f"dl_uuid_{track_uuid}",
                    )
                ]
            )

        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔙 Volver al Menú",
                    switch_inline_query_current_chat="",
                )
            ]
        )

        await status_msg.edit_text(
            f"💿 *Canciones del Álbum {album_title}:*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    except Exception as e:
        logger.error("Error view_album: %s", e)
        await update.message.reply_text(
            "❌ Error al obtener canciones del álbum. Intenta de nuevo."
        )


async def handle_download_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Maneja el click en los botones de canciones de artistas/álbumes"""
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("dl_uuid_"):
        return

    uuid_key = query.data.removeprefix("dl_uuid_")
    track_info = track_cache.get(uuid_key)

    if not track_info:
        await query.message.reply_text(
            "❌ La sesión de este botón ha expirado. Busca de nuevo con /start."
        )
        return

    await _start_download_from_callback(
        query, context, track_info["title"], track_info["artist"]
    )


async def _start_download(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    track: str,
    artist: str,
):
    """Lógica común de descarga para comandos de texto"""
    msg = await update.message.reply_text(
        f"🔎 Buscando: *{track}*...", quote=True, parse_mode="Markdown"
    )
    await _process_download(msg, context, track, artist)


async def _start_download_from_callback(
    query: CallbackQuery,
    context: ContextTypes.DEFAULT_TYPE,
    track: str,
    artist: str,
):
    """Lógica común de descarga para callbacks"""
    msg = await query.message.reply_text(
        f"🔎 Buscando: *{track}*...", parse_mode="Markdown"
    )
    await _process_download(msg, context, track, artist)


async def _process_download(status_message, context, track_name, artist_name):
    """Proceso de descarga compartido"""
    try:
        await status_message.edit_text(
            f"⏬ *Descargando:*\n"
            f"🎵 {track_name}\n"
            f"👤 {artist_name}\n\n"
            f"⏳ Puede tardar 1-2 minutos...",
            parse_mode="Markdown",
        )

        file_path = await asyncio.to_thread(
            downloader.download_track, track_name, artist_name
        )

        if not file_path:
            await status_message.edit_text(
                f"❌ *Error al descargar*\n\n"
                f"No se pudo descargar: {track_name} - {artist_name}\n"
                f"Intenta con otra canción.",
                parse_mode="Markdown",
            )
            return

        await status_message.edit_text("📤 Enviando audio...")

        with open(file_path, "rb") as f:
            await context.bot.send_audio(
                chat_id=status_message.chat_id,
                audio=f,
                title=track_name,
                performer=artist_name,
                caption=f"🎵 {track_name}\n👤 {artist_name}",
                write_timeout=120,
                read_timeout=120,
                connect_timeout=60,
            )

        # Menú completo al finalizar
        keyboard = [
            [
                InlineKeyboardButton(
                    "🎵 Buscar por Canción",
                    switch_inline_query_current_chat="",
                )
            ],
            [
                InlineKeyboardButton(
                    "👤 Buscar por Artista",
                    switch_inline_query_current_chat="artist: ",
                )
            ],
            [
                InlineKeyboardButton(
                    "💿 Buscar por Álbum",
                    switch_inline_query_current_chat="album: ",
                )
            ],
        ]

        await status_message.edit_text(
            "✅ *Descarga completada*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        downloader.cleanup_file(file_path)

    except Exception as e:
        logger.error("Error en descarga: %s", e)
        await status_message.edit_text(f"❌ Error: {e}")
