from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎵 Buscar por Canción", switch_inline_query_current_chat="")],
        [InlineKeyboardButton("👤 Buscar por Artista", switch_inline_query_current_chat="artist: ")],
        [InlineKeyboardButton("💿 Buscar por Álbum", switch_inline_query_current_chat="album: ")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🎧 *¡Bienvenido al Bot de Música!*\n\n"
        "Selecciona cómo quieres buscar y escribe el nombre para ver resultados en tiempo real:"
    )
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode="Markdown")
