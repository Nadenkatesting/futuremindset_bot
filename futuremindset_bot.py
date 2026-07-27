#!/usr/bin/env python3
"""
Future Mindset — Telegram-бот для записи на консультации
Стиль и визаж | Онлайн по всей России

Упрощённая версия: polling в фоне + Flask health-check
"""

import os
import logging
import threading
from datetime import datetime
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

# ═══════════════════════════════════════════════════════════════
# НАСТРОЙКИ
# ═══════════════════════════════════════════════════════════════

BOT_TOKEN = "8733901363:AAENe2LFHFg1cCl0WSdPgjLWfHq5aL2YWYk"
ADMIN_ID = 716337525

SERVICES = {
    "style": {
        "name": "Консультация по стилю",
        "price": "4 900 ₽",
        "duration": "60–90 мин",
        "description": "Капсула, шопинг-лист, PDF-гид"
    },
    "makeup": {
        "name": "Консультация по визажу",
        "price": "3 900 ₽",
        "duration": "60 мин",
        "description": "Цветотип, макияж, уход, список косметики"
    }
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# КЛАВИАТУРЫ
# ═══════════════════════════════════════════════════════════════

def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👗 Консультация по стилю — 4 900 ₽", callback_data="service:style")],
        [InlineKeyboardButton("💄 Консультация по визажу — 3 900 ₽", callback_data="service:makeup")],
        [InlineKeyboardButton("❓ Задать вопрос", url="https://t.me/iwownadenka")]
    ])

def confirm_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Всё верно, записаться", callback_data="confirm:yes"),
         InlineKeyboardButton("🔄 Заполнить заново", callback_data="confirm:restart")]
    ])

def admin_kb(user_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Принять заявку", callback_data=f"admin:accept:{user_id}"),
         InlineKeyboardButton("💬 Написать клиенту", url=f"tg://user?id={user_id}")]
    ])

def contact_kb():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Отправить номер", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

# ═══════════════════════════════════════════════════════════════
# ОБРАБОТЧИКИ
# ═══════════════════════════════════════════════════════════════

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога"""
    user = update.effective_user
    context.user_data.clear()
    context.user_data["state"] = "menu"
    
    await update.message.reply_html(
        f"Привет, {user.first_name}! 👋\n\n"
        f"Добро пожаловать в <b>Future Mindset</b> — пространство стиля и красоты.\n\n"
        f"Я помогу записать вас на онлайн-консультацию.\n"
        f"Выберите услугу ниже 👇",
        reply_markup=main_menu_kb()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data.startswith("service:"):
        service_key = data.split(":")[1]
        service = SERVICES[service_key]
        
        context.user_data["service_key"] = service_key
        context.user_data["service_name"] = service["name"]
        context.user_data["service_price"] = service["price"]
        context.user_data["state"] = "waiting_name"
        
        text = (
            f"✨ <b>{service['name']}</b>\n"
            f"💰 Стоимость: <b>{service['price']}</b>\n"
            f"⏱ Длительность: {service['duration']}\n"
            f"📦 Входит: {service['description']}\n\n"
            f"Отличный выбор! Теперь расскажите немного о себе.\n\n"
            f"Как вас зовут? (имя, которым удобно обращаться)"
        )
        await query.edit_message_text(text, parse_mode="HTML")
    
    elif data == "confirm:yes":
        await send_booking(update, context)
    
    elif data == "confirm:restart":
        context.user_data.clear()
        context.user_data["state"] = "menu"
        await query.edit_message_text(
            "Давайте начнём сначала! Выберите услугу:",
            reply_markup=main_menu_kb()
        )
    
    elif data.startswith("admin:accept:"):
        await admin_accept(update, context)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений по состоянию"""
    state = context.user_data.get("state", "menu")
    text = update.message.text.strip()
    
    if state == "waiting_name":
        context.user_data["name"] = text
        context.user_data["state"] = "waiting_phone"
        await update.message.reply_text(
            "Отлично! Теперь отправьте ваш номер телефона:",
            reply_markup=contact_kb()
        )
    
    elif state == "waiting_phone":
        context.user_data["phone"] = text
        context.user_data["state"] = "waiting_city"
        await update.message.reply_text(
            "📍 Из какого вы города? (это поможет подобрать магазины и бренды)",
            reply_markup=ReplyKeyboardRemove()
        )
    
    elif state == "waiting_city":
        context.user_data["city"] = text
        context.user_data["state"] = "waiting_comment"
        await update.message.reply_text(
            "💬 Есть ли у вас особые пожелания или вопросы перед консультацией?\n"
            "(можно написать кратко или отправить «нет»)",
            reply_markup=ReplyKeyboardRemove()
        )
    
    elif state == "waiting_comment":
        context.user_data["comment"] = text if text.lower() not in ("нет", "-", "no") else "—"
        context.user_data["state"] = "confirming"
        
        data = context.user_data
        summary = (
            f"📋 <b>Проверьте вашу заявку:</b>\n\n"
            f"👤 Имя: <b>{data['name']}</b>\n"
            f"📱 Телефон: <code>{data['phone']}</code>\n"
            f"📍 Город: {data['city']}\n"
            f"💄 Услуга: <b>{data['service_name']}</b>\n"
            f"💰 Стоимость: {data['service_price']}\n"
            f"💬 Комментарий: {data['comment']}\n\n"
            f"Всё верно?"
        )
        await update.message.reply_html(summary, reply_markup=confirm_kb())
    
    else:
        await update.message.reply_text(
            "Я не совсем понял 😊\n"
            "Давайте начнём с выбора услуги:",
            reply_markup=main_menu_kb()
        )

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка отправки контакта"""
    state = context.user_data.get("state", "")
    
    if state == "waiting_phone":
        context.user_data["phone"] = update.message.contact.phone_number
        context.user_data["state"] = "waiting_city"
        await update.message.reply_text(
            "📍 Из какого вы города? (это поможет подобрать магазины и бренды)",
            reply_markup=ReplyKeyboardRemove()
        )

async def send_booking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправка заявки админу"""
    query = update.callback_query
    data = context.user_data
    user = query.from_user
    
    admin_text = (
        f"🔔 <b>НОВАЯ ЗАЯВКА!</b>\n{'═' * 30}\n\n"
        f"👤 <b>Клиент:</b> {data.get('name', '—')}\n"
        f"📱 <b>Телефон:</b> <code>{data.get('phone', '—')}</code>\n"
        f"📍 <b>Город:</b> {data.get('city', '—')}\n"
        f"🆔 <b>Telegram:</b> @{user.username or 'нет username'}\n"
        f"🔗 <b>ID:</b> <code>{user.id}</code>\n\n"
        f"💄 <b>Услуга:</b> {data.get('service_name', '—')}\n"
        f"💰 <b>Стоимость:</b> {data.get('service_price', '—')}\n"
        f"💬 <b>Комментарий:</b> {data.get('comment', '—')}\n\n"
        f"⏰ <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    try:
        await context.bot.send_message(
            ADMIN_ID, admin_text, parse_mode="HTML",
            reply_markup=admin_kb(user.id)
        )
        
        await query.edit_message_text(
            f"✅ <b>Заявка отправлена!</b>\n\n"
            f"Спасибо, {data.get('name', '')}! Наденька получила вашу заявку на <b>{data.get('service_name', '')}</b>.\n"
            f"Свяжется с вами в течение <b>2 часов</b>.\n\n"
            f"📱 Ваш телефон: <code>{data.get('phone', '')}</code>\n"
            f"💰 К оплате: <b>{data.get('service_price', '')}</b>\n\n"
            f"Если есть вопросы — пишите: @iwownadenka",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        await query.edit_message_text(
            "⚠️ Произошла ошибка. Напишите напрямую: @iwownadenka",
            parse_mode="HTML"
        )
    
    context.user_data.clear()

async def admin_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Админ принял заявку"""
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("⛔ Нет доступа", show_alert=True)
        return
    await query.answer()
    user_id = int(query.data.split(":")[2])
    try:
        await context.bot.send_message(
            user_id,
            "✅ <b>Ваша заявка принята!</b>\n\n"
            "Наденька свяжется с вами для уточнения деталей и отправки ссылки на Zoom.\n"
            "Спасибо за доверие! 💕",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить клиента {user_id}: {e}")
    await query.edit_message_text(
        query.message.text + "\n\n✅ <b>Заявка принята</b>",
        parse_mode="HTML"
    )

# ═══════════════════════════════════════════════════════════════
# СОЗДАНИЕ ПРИЛОЖЕНИЯ
# ═══════════════════════════════════════════════════════════════

application = Application.builder().token(BOT_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.CONTACT, contact_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

# ═══════════════════════════════════════════════════════════════
# FLASK — HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

app = Flask(__name__)

@app.route('/')
def health():
    return "Future Mindset Bot is running! 💕"

@app.route('/health')
def health_detailed():
    return {"status": "ok", "bot": "futuremindset_bot"}

# ═══════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════

def run_bot():
    """Запуск бота в фоновом потоке"""
    logger.info("🤖 Запуск polling бота...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Flask health-check на порту {port}")
    app.run(host='0.0.0.0', port=port)
