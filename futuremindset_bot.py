#!/usr/bin/env python3
"""
Future Mindset — Telegram-бот для записи на консультации
Стиль и визаж | Онлайн по всей России
"""

import asyncio
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ConversationHandler, filters, ContextTypes
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

(CHOOSING_SERVICE, ENTERING_NAME, ENTERING_PHONE, ENTERING_CITY,
 ENTERING_COMMENT, CONFIRMING) = range(6)

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
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.first_name}! 👋\n\n"
        f"Добро пожаловать в <b>Future Mindset</b> — пространство стиля и красоты.\n\n"
        f"Я помогу записать вас на онлайн-консультацию.\n"
        f"Выберите услугу ниже 👇",
        reply_markup=main_menu_kb()
    )
    return CHOOSING_SERVICE

async def service_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    service_key = query.data.split(":")[1]
    service = SERVICES[service_key]
    
    context.user_data["service_key"] = service_key
    context.user_data["service_name"] = service["name"]
    context.user_data["service_price"] = service["price"]
    
    text = (
        f"✨ <b>{service['name']}</b>\n"
        f"💰 Стоимость: <b>{service['price']}</b>\n"
        f"⏱ Длительность: {service['duration']}\n"
        f"📦 Входит: {service['description']}\n\n"
        f"Отличный выбор! Теперь расскажите немного о себе.\n\n"
        f"Как вас зовут? (имя, которым удобно обращаться)"
    )
    
    await query.edit_message_text(text, parse_mode="HTML")
    return ENTERING_NAME

async def enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text.strip()
    await update.message.reply_text(
        "Отлично! Теперь отправьте ваш номер телефона:",
        reply_markup=contact_kb()
    )
    return ENTERING_PHONE

async def enter_phone_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.contact.phone_number
    await update.message.reply_text(
        "📍 Из какого вы города? (это поможет подобрать магазины и бренды)",
        reply_markup=ReplyKeyboardRemove()
    )
    return ENTERING_CITY

async def enter_phone_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text.strip()
    await update.message.reply_text(
        "📍 Из какого вы города?",
        reply_markup=ReplyKeyboardRemove()
    )
    return ENTERING_CITY

async def enter_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text.strip()
    await update.message.reply_text(
        "💬 Есть ли у вас особые пожелания или вопросы перед консультацией?\n"
        "(можно написать кратко или отправить «нет»)",
        reply_markup=ReplyKeyboardRemove()
    )
    return ENTERING_COMMENT

async def enter_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    comment = update.message.text.strip()
    context.user_data["comment"] = comment if comment.lower() not in ("нет", "-", "no") else "—"
    
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
    return CONFIRMING

async def confirm_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = context.user_data
    user = query.from_user
    
    admin_text = (
        f"🔔 <b>НОВАЯ ЗАЯВКА!</b>\n{'═' * 30}\n\n"
        f"👤 <b>Клиент:</b> {data['name']}\n"
        f"📱 <b>Телефон:</b> <code>{data['phone']}</code>\n"
        f"📍 <b>Город:</b> {data['city']}\n"
        f"🆔 <b>Telegram:</b> @{user.username or 'нет username'}\n"
        f"🔗 <b>ID:</b> <code>{user.id}</code>\n\n"
        f"💄 <b>Услуга:</b> {data['service_name']}\n"
        f"💰 <b>Стоимость:</b> {data['service_price']}\n"
        f"💬 <b>Комментарий:</b> {data['comment']}\n\n"
        f"⏰ <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    try:
        await context.bot.send_message(
            ADMIN_ID, admin_text, parse_mode="HTML",
            reply_markup=admin_kb(user.id)
        )
        
        await query.edit_message_text(
            f"✅ <b>Заявка отправлена!</b>\n\n"
            f"Спасибо, {data['name']}! Наденька получила вашу заявку на <b>{data['service_name']}</b>.\n"
            f"Свяжется с вами в течение <b>2 часов</b>.\n\n"
            f"📱 Ваш телефон: <code>{data['phone']}</code>\n"
            f"💰 К оплате: <b>{data['service_price']}</b>\n\n"
            f"Если есть вопросы — пишите: @iwownadenka",
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await query.edit_message_text(
            "⚠️ Произошла ошибка. Напишите напрямую: @iwownadenka",
            parse_mode="HTML"
        )
    
    return ConversationHandler.END

async def confirm_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text(
        "Давайте начнём сначала! Выберите услугу:",
        reply_markup=main_menu_kb()
    )
    return CHOOSING_SERVICE

async def admin_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Диалог отменён. Начните заново — /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Я не совсем понял 😊\nДавайте начнём с выбора услуги:",
        reply_markup=main_menu_kb()
    )

# ═══════════════════════════════════════════════════════════════
# ЗАПУСК — ИСПРАВЛЕННЫЙ ДЛЯ PYTHON 3.14
# ═══════════════════════════════════════════════════════════════

async def main():
    logger.info("🤖 Бот Future Mindset запущен!")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_SERVICE: [CallbackQueryHandler(service_choice, pattern="^service:")],
            ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_name)],
            ENTERING_PHONE: [
                MessageHandler(filters.CONTACT, enter_phone_contact),
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone_text)
            ],
            ENTERING_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_city)],
            ENTERING_COMMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_comment)],
            CONFIRMING: [
                CallbackQueryHandler(confirm_yes, pattern="^confirm:yes$"),
                CallbackQueryHandler(confirm_restart, pattern="^confirm:restart$")
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=True,
    )
    
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(admin_accept, pattern="^admin:accept:"))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, unknown_message))
    
    # Исправленный запуск для Python 3.14
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    
    # Держим бота запущенным
    stop_event = asyncio.Event()
    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
