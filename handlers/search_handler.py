import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import asyncio
from services.music_search import music_service
from services.downloader import downloader

logger = logging.getLogger(__name__)

# Estados del ConversationHandler
SEARCH_BY_NAME, SEARCH_BY_ARTIST, SEARCH_BY_ALBUM = range(3)
SELECTING_ARTIST, SELECTING_ALBUM, SELECTING_TRACK = range(3, 6)

# Patrón para callbacks que maneja este ConversationHandler
CONV_CALLBACK_PATTERN = r"^(search_by_name|search_by_artist|search_by_album|start_search|cancel|track_\d+|artist_\d+|album_\d+)$"


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja la selección del tipo de búsqueda desde el menú principal"""
    query = update.callback_query
    await query.answer()

    if query.data == "search_by_name":
        await query.edit_message_text(
            "🔍 *Escribe el nombre de la canción:*", parse_mode="Markdown"
        )
        return SEARCH_BY_NAME
    elif query.data == "search_by_artist":
        await query.edit_message_text(
            "🔍 *Escribe el nombre del artista:*", parse_mode="Markdown"
        )
        return SEARCH_BY_ARTIST
    elif query.data == "search_by_album":
        await query.edit_message_text(
            "🔍 *Escribe el nombre del álbum:*", parse_mode="Markdown"
        )
        return SEARCH_BY_ALBUM
    elif query.data == "start_search":
        keyboard = [
            [
                InlineKeyboardButton(
                    "🎵 Buscar Canción/Artista en Vivo",
                    switch_inline_query_current_chat="",
                )
            ],
            [InlineKeyboardButton("❌ Cancelar", callback_data="cancel")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Presiona el botón y escribe para buscar:", reply_markup=reply_markup
        )
        return ConversationHandler.END
    elif query.data == "cancel":
        await query.edit_message_text("❌ Búsqueda cancelada.")
        return ConversationHandler.END

    # Manejar callbacks de selección que llegaron con sesión expirada
    if query.data.startswith(("track_", "artist_", "album_")):
        await query.edit_message_text(
            "⚠️ *La sesión ha expirado*\n"
            "Por favor, inicia una nueva búsqueda con /start",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    await query.edit_message_text("❌ Opción no válida. Usa /start para reiniciar.")
    return ConversationHandler.END


async def handle_song_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Busca canciones por nombre"""
    user_input = update.message.text
    await update.message.reply_text(
        f"🔎 Buscando: *{user_input}*...", parse_mode="Markdown"
    )

    tracks = music_service.search_tracks(user_input, limit=10)

    if not tracks:
        await update.message.reply_text(
            "❌ No se encontraron canciones con ese nombre."
        )
        return ConversationHandler.END

    context.user_data["search_results"] = tracks
    context.user_data["search_type"] = "track"

    keyboard = []
    for idx, track in enumerate(tracks):
        duration = music_service.format_duration(track["duration"])
        button_text = f"🎵 {track['title']} - {track['artist']} ({duration})"
        keyboard.append(
            [InlineKeyboardButton(button_text, callback_data=f"track_{idx}")]
        )

    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📋 *Resultados encontrados:*\nSelecciona una canción:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return SELECTING_TRACK


async def handle_artist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Busca artistas por nombre"""
    user_input = update.message.text
    await update.message.reply_text(
        f"🔎 Buscando artistas: *{user_input}*...", parse_mode="Markdown"
    )

    artists = music_service.search_artists(user_input, limit=10)

    if not artists:
        await update.message.reply_text(
            "❌ No se encontraron artistas con ese nombre."
        )
        return ConversationHandler.END

    context.user_data["search_results"] = artists
    context.user_data["search_type"] = "artist"

    keyboard = []
    for idx, artist in enumerate(artists):
        albums = artist.get("nb_album", 0)
        button_text = f"👤 {artist['name']} ({albums} álbumes)"
        keyboard.append(
            [InlineKeyboardButton(button_text, callback_data=f"artist_{idx}")]
        )

    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📋 *Artistas encontrados:*\nSelecciona un artista:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return SELECTING_ARTIST


async def handle_album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Busca álbumes por nombre"""
    user_input = update.message.text
    await update.message.reply_text(
        f"🔎 Buscando álbumes: *{user_input}*...", parse_mode="Markdown"
    )

    albums = music_service.search_albums(user_input, limit=10)

    if not albums:
        await update.message.reply_text(
            "❌ No se encontraron álbumes con ese nombre."
        )
        return ConversationHandler.END

    context.user_data["search_results"] = albums
    context.user_data["search_type"] = "album"

    keyboard = []
    for idx, album in enumerate(albums):
        tracks = album.get("nb_tracks", 0)
        button_text = f"💿 {album['title']} - {album['artist']} ({tracks} canciones)"
        keyboard.append(
            [InlineKeyboardButton(button_text, callback_data=f"album_{idx}")]
        )

    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📋 *Álbumes encontrados:*\nSelecciona un álbum:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return SELECTING_ALBUM


async def _handle_cancel_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Maneja el botón cancelar en cualquier estado de selección"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("❌ Búsqueda cancelada.")
    return ConversationHandler.END


async def handle_artist_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Maneja la selección de un artista"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Búsqueda cancelada.")
        return ConversationHandler.END

    try:
        idx = int(query.data.split("_")[1])
    except (IndexError, ValueError):
        await query.edit_message_text("❌ Error: selección no válida.")
        return ConversationHandler.END

    artists = context.user_data.get("search_results", [])

    if idx >= len(artists):
        await query.edit_message_text("❌ Error: Artista no válido.")
        return ConversationHandler.END

    selected_artist = artists[idx]
    await query.edit_message_text(
        f"⏳ Obteniendo canciones de *{selected_artist['name']}*...",
        parse_mode="Markdown",
    )

    tracks = music_service.get_artist_top_tracks(selected_artist["id"], limit=15)

    if not tracks:
        await query.edit_message_text(
            f"❌ No se encontraron canciones de {selected_artist['name']}."
        )
        return ConversationHandler.END

    context.user_data["search_results"] = tracks
    context.user_data["search_type"] = "track"

    keyboard = []
    for idx, track in enumerate(tracks):
        duration = music_service.format_duration(track["duration"])
        button_text = f"🎵 {track['title']} ({duration})"
        keyboard.append(
            [InlineKeyboardButton(button_text, callback_data=f"track_{idx}")]
        )

    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"🎤 *Canciones de {selected_artist['name']}:*\nSelecciona una canción:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return SELECTING_TRACK


async def handle_album_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Maneja la selección de un álbum"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Búsqueda cancelada.")
        return ConversationHandler.END

    try:
        idx = int(query.data.split("_")[1])
    except (IndexError, ValueError):
        await query.edit_message_text("❌ Error: selección no válida.")
        return ConversationHandler.END

    albums = context.user_data.get("search_results", [])

    if idx >= len(albums):
        await query.edit_message_text("❌ Error: Álbum no válido.")
        return ConversationHandler.END

    selected_album = albums[idx]
    await query.edit_message_text(
        f"⏳ Obteniendo canciones del álbum *{selected_album['title']}*...",
        parse_mode="Markdown",
    )

    tracks = music_service.get_album_tracks(selected_album["id"])

    if not tracks:
        await query.edit_message_text(
            f"❌ No se encontraron canciones en el álbum {selected_album['title']}."
        )
        return ConversationHandler.END

    context.user_data["search_results"] = tracks
    context.user_data["search_type"] = "track"

    keyboard = []
    for idx, track in enumerate(tracks):
        duration = music_service.format_duration(track["duration"])
        button_text = f"🎵 {track['title']} ({duration})"
        keyboard.append(
            [InlineKeyboardButton(button_text, callback_data=f"track_{idx}")]
        )

    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"💿 *Canciones de {selected_album['title']}:*\nSelecciona una canción:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )
    return SELECTING_TRACK


async def handle_song_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Maneja la selección de una canción y procede a descargarla"""
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text("❌ Descarga cancelada.")
        return ConversationHandler.END

    try:
        idx = int(query.data.split("_")[1])
    except (IndexError, ValueError):
        await query.edit_message_text("❌ Error: selección no válida.")
        return ConversationHandler.END

    tracks = context.user_data.get("search_results", [])

    if idx >= len(tracks):
        await query.edit_message_text("❌ Error: Canción no válida.")
        return ConversationHandler.END

    selected_track = tracks[idx]

    await query.edit_message_text(
        f"⏬ *Descargando:*\n"
        f"🎵 {selected_track['title']}\n"
        f"👤 {selected_track['artist']}\n\n"
        f"⏳ Puede tardar 1-2 minutos...",
        parse_mode="Markdown",
    )

    file_path = await asyncio.to_thread(
        downloader.download_track,
        selected_track["title"],
        selected_track["artist"],
    )

    if not file_path:
        await query.edit_message_text(
            f"❌ *Error al descargar la canción*\n\n"
            f"No se pudo descargar: {selected_track['title']} - {selected_track['artist']}\n"
            f"Intenta con otra canción o verifica los logs.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    try:
        with open(file_path, "rb") as audio_file:
            await context.bot.send_audio(
                chat_id=query.message.chat_id,
                audio=audio_file,
                title=selected_track["title"],
                performer=selected_track["artist"],
                caption=(
                    f"🎵 {selected_track['title']}\n"
                    f"👤 {selected_track['artist']}\n"
                    f"💿 {selected_track['album']}"
                ),
                write_timeout=120,
                read_timeout=120,
                connect_timeout=60,
            )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔍 Nueva Búsqueda",
                    switch_inline_query_current_chat="",
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"✅ *Descarga completada*\n\n"
            f"🎵 {selected_track['title']}\n"
            f"👤 {selected_track['artist']}",
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )

    except Exception as e:
        logger.error("Error enviando audio: %s", e)
        await query.edit_message_text(
            f"❌ *Error al enviar el archivo*\n\nBot Error: {e}",
            parse_mode="Markdown",
        )
    finally:
        downloader.cleanup_file(file_path)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancela la conversación actual"""
    await update.message.reply_text(
        "❌ Operación cancelada. Usa /start para comenzar de nuevo."
    )
    return ConversationHandler.END


# Definir el ConversationHandler con filtro de patrón en el entry point
conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(button_handler, pattern=CONV_CALLBACK_PATTERN),
    ],
    states={
        SEARCH_BY_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_song_name)
        ],
        SEARCH_BY_ARTIST: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_artist)
        ],
        SEARCH_BY_ALBUM: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_album)
        ],
        SELECTING_ARTIST: [
            CallbackQueryHandler(_handle_cancel_callback, pattern=r"^cancel$"),
            CallbackQueryHandler(handle_artist_selection, pattern=r"^artist_\d+$"),
        ],
        SELECTING_ALBUM: [
            CallbackQueryHandler(_handle_cancel_callback, pattern=r"^cancel$"),
            CallbackQueryHandler(handle_album_selection, pattern=r"^album_\d+$"),
        ],
        SELECTING_TRACK: [
            CallbackQueryHandler(_handle_cancel_callback, pattern=r"^cancel$"),
            CallbackQueryHandler(handle_song_selection, pattern=r"^track_\d+$"),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel),
        CommandHandler("start", cancel),  # /start también cancela la conversación activa
    ],
    per_message=True,
)
