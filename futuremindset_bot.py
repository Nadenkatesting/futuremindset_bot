import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логов (чтобы видеть, что происходит)
logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

# ── СЮДА ВСТАВЬТЕ ТОКЕН ОТ @BOTFATHER ──
TOKEN = os.environ.get("BOT_TOKEN", "ВАШ_ТОКЕН_СЮДА")

# ── СЮДА ВСТАВЬТЕ АДРЕС ВАШЕГО САЙТА НА RENDER ──
# Например: https://futuremindset-bot-1-j5ft.onrender.com
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "ВАШ_URL_СЮДА").rstrip("/")

PORT = int(os.environ.get("PORT", "10000"))
WEBHOOK_PATH = f"/{TOKEN}"


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот работает ✅")


# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Команды: /start, /help")


# Ответ на любой текст
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Вы написали: {update.message.text}")


# Главная функция
def main():
    # Создаём приложение
    app = Application.builder().token(TOKEN).build()

    # Регистрируем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Запускаем webhook (встроенный сервер, никакого Flask!)
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=f"{WEBHOOK_URL}{WEBHOOK_PATH}",
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
