import os
import logging
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ── Логирование ─────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ── Переменные окружения ──────────────────────────────────
def require_env(key: str) -> str:
    value = os.environ.get(key)
    if not value:
        logger.error(f"❌ Переменная окружения {key} не задана!")
        sys.exit(1)
    return value


TOKEN = require_env("BOT_TOKEN")
WEBHOOK_HOST = require_env("WEBHOOK_URL").rstrip("/")   # https://futuremindset-bot-...onrender.com
PORT = int(os.environ.get("PORT", "10000"))

# Путь webhook'а — токен служит секретным сегментом URL
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"


# ── Ваши обработчики (замените на свои) ───────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 Бот работает через нативный webhook на Render!\n\n"
        "Отправьте любое текстовое сообщение — получите эхо."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Доступные команды: /start, /help")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    await update.message.reply_text(f"📨 Эхо: <code>{text}</code>", parse_mode="HTML")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Ошибка при обработке обновления:", exc_info=context.error)


# ── Точка входа ───────────────────────────────────────────
def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    application.add_error_handler(error_handler)

    logger.info(f"🚀 Запуск webhook-сервера на 0.0.0.0:{PORT}")
    logger.info(f"🔗 Telegram будет слать обновления на: {WEBHOOK_URL}")

    # ⬇️ ЕДИНСТВЕННЫЙ нужный вызов — блокирующий, встроенный aiohttp-сервер
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,        # путь, на котором слушает сервер
        webhook_url=WEBHOOK_URL,      # URL, который регистрируется в Telegram
        secret_token=TOKEN,           # X-Telegram-Bot-Api-Secret-Token
        drop_pending_updates=True,    # сбросить накопившиеся обновления при старте
    )


if __name__ == "__main__":
    main()
