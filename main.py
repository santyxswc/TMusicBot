import atexit
import asyncio
import logging
import os
import subprocess
import sys
from pathlib import Path

from telegram import Update
from telegram.error import Conflict
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    InlineQueryHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from config import TOKEN
from handlers.start_handler import start
from handlers.search_handler import conv_handler
from handlers.inline_handler import (
    inline_query,
    handle_inline_result,
    handle_view_artist,
    handle_view_album,
    handle_download_callback,
)

LOCK_FILE = Path(__file__).parent / ".bot.lock"
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _is_process_running(pid: int) -> bool:
    result = subprocess.run(
        ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
        capture_output=True,
        text=True,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return str(pid) in result.stdout


def ensure_single_instance():
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            if _is_process_running(pid):
                print(f"[ERROR] Ya hay una instancia del bot corriendo (PID {pid}).")
                print("Cierra la otra terminal antes de volver a iniciar el bot.")
                sys.exit(1)
        except (ValueError, OSError):
            pass
    LOCK_FILE.write_text(str(os.getpid()), encoding="utf-8")
    atexit.register(lambda: LOCK_FILE.unlink(missing_ok=True))


async def error_handler(update: object, context) -> None:
    if isinstance(context.error, Conflict):
        logger.warning(
            "Otra instancia del bot detectada. Solo debe haber una en ejecución."
        )
        return
    logger.error("Error no manejado", exc_info=context.error)


def main():
    if TOKEN == "":
        print("[ERROR] Por favor configura el TOKEN en el archivo .env")
        print("Obten tu token desde @BotFather en Telegram")
        return

    ensure_single_instance()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_error_handler(error_handler)

    # 1. Comando /start
    app.add_handler(CommandHandler("start", start))

    # 2. Callbacks de descarga desde inline (dl_uuid_*) — ANTES del conv_handler
    #    para que no sean interceptados por el ConversationHandler
    app.add_handler(
        CallbackQueryHandler(handle_download_callback, pattern=r"^dl_uuid_")
    )

    # 3. ConversationHandler para búsqueda paso a paso
    #    (tiene filtro de patrón, no intercepta dl_uuid_*)
    app.add_handler(conv_handler)

    # 4. Inline query handler
    app.add_handler(InlineQueryHandler(inline_query))

    # 5. Handlers de texto para resultados inline
    app.add_handler(
        MessageHandler(filters.Regex(r"^/dl_track"), handle_inline_result)
    )
    app.add_handler(
        MessageHandler(filters.Regex(r"^/view_artist"), handle_view_artist)
    )
    app.add_handler(
        MessageHandler(filters.Regex(r"^/view_album"), handle_view_album)
    )

    print("[OK] Bot de musica corriendo...")
    print("Abre Telegram y escribe /start para comenzar")
    print("Presiona Ctrl+C para detener el bot")

    try:
        asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
