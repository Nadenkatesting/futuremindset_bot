#!/usr/bin/env python3
"""
Future Mindset — Telegram-бот для записи на консультации
Стиль и визаж | Онлайн по всей России

Установка:
    pip install -r requirements.txt

Запуск:
    python futuremindset_bot.py
"""

import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ═══════════════════════════════════════════════════════════════
# НАСТРОЙКИ
# ═══════════════════════════════════════════════════════════════

BOT_TOKEN = "8733901363:AAENe2LFHFg1cCl0WSdPgjLWfHq5aL2YWYk"
ADMIN_ID = 716337525  # Nadenka Kasianenko

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

# ═══════════════════════════════════════════════════════════════
# ЛОГИРОВАНИЕ
# ═══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# FSM — МАШИНА СОСТОЯНИЙ
# ═══════════════════════════════════════════════════════════════

class BookingState(StatesGroup):
    choosing_service = State()
    entering_name = State()
    entering_phone = State()
    entering_city = State()
    entering_comment = State()
    confirming = State()

# ═══════════════════════════════════════════════════════════════
# ИНИЦИАЛИЗАЦИЯ
# ═══════════════════════════════════════════════════════════════

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ═══════════════════════════════════════════════════════════════
# КЛАВИАТУРЫ
# ═══════════════════════════════════════════════════════════════

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="👗 Консультация по стилю — 4 900 ₽",
                callback_data="service:style"
            )
        ],
        [
            InlineKeyboardButton(
                text="💄 Консультация по визажу — 3 900 ₽",
                callback_data="service:makeup"
            )
        ],
        [
            InlineKeyboardButton(
                text="❓ Задать вопрос",
                url="https://t.me/iwownadenka"
            )
        ]
    ])

def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Всё верно, записаться", callback_data="confirm:yes"),
            InlineKeyboardButton(text="🔄 Заполнить заново", callback_data="confirm:restart")
        ]
    ])

def admin_kb(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Принять заявку",
                callback_data=f"admin:accept:{user_id}"
            ),
            InlineKeyboardButton(
                text="💬 Написать клиенту",
                url=f"tg://user?id={user_id}"
            )
        ]
    ])

def contact_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# ═══════════════════════════════════════════════════════════════
# ОБРАБОТЧИКИ КОМАНД
# ═══════════════════════════════════════════════════════════════

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()

    welcome_text = (
        f"Привет, {message.from_user.first_name}! 👋\n\n"
        f"Добро пожаловать в <b>Future Mindset</b> — пространство стиля и красоты.\n\n"
        f"Я помогу записать вас на онлайн-консультацию.\n"
        f"Выберите услугу ниже 👇"
    )

    await message.answer(
        welcome_text,
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "📋 <b>Как это работает:</b>\n\n"
        "1️⃣ Выберите услугу\n"
        "2️⃣ Оставьте контакты\n"
        "3️⃣ Наденька свяжется с вами в течение 2 часов\n"
        "4️⃣ Согласуем удобное время для Zoom-консультации\n\n"
        "❓ По вопросам пишите: @iwownadenka",
        parse_mode="HTML"
    )

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет доступа.")
        return

    await message.answer(
        "👩‍💼 <b>Панель администратора</b>\n\n"
        "Команды:\n"
        "/stats — статистика заявок\n"
        "/broadcast — рассылка сообщений",
        parse_mode="HTML"
    )

# ═══════════════════════════════════════════════════════════════
# INLINE КНОПКИ
# ═══════════════════════════════════════════════════════════════

@dp.callback_query(F.data.startswith("service:"))
async def process_service_choice(callback: types.CallbackQuery, state: FSMContext):
    service_key = callback.data.split(":")[1]
    service = SERVICES[service_key]

    await state.update_data(
        service_key=service_key,
        service_name=service["name"],
        service_price=service["price"]
    )

    text = (
        f"✨ <b>{service['name']}</b>\n"
        f"💰 Стоимость: <b>{service['price']}</b>\n"
        f"⏱ Длительность: {service['duration']}\n"
        f"📦 Входит: {service['description']}\n\n"
        f"Отличный выбор! Теперь расскажите немного о себе.\n\n"
        f"Как вас зовут? (имя, которым удобно обращаться)"
    )

    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(BookingState.entering_name)
    await callback.answer()

# ═══════════════════════════════════════════════════════════════
# СБОР ДАННЫХ (FSM)
# ═══════════════════════════════════════════════════════════════

@dp.message(BookingState.entering_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())

    await message.answer(
        "Отлично! Теперь отправьте ваш номер телефона, чтобы Наденька могла с вами связаться:",
        reply_markup=contact_kb()
    )
    await state.set_state(BookingState.entering_phone)

@dp.message(BookingState.entering_phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)

    await message.answer(
        "📍 Из какого вы города? (это поможет подобрать магазины и бренды)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(BookingState.entering_city)

@dp.message(BookingState.entering_phone)
async def process_phone_text(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    await state.update_data(phone=phone)

    await message.answer(
        "📍 Из какого вы города? (это поможет подобрать магазины и бренды)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(BookingState.entering_city)

@dp.message(BookingState.entering_city)
async def process_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text.strip())

    await message.answer(
        "💬 Есть ли у вас особые пожелания или вопросы перед консультацией?\n"
        "(можно написать кратко или отправить «нет»)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(BookingState.entering_comment)

@dp.message(BookingState.entering_comment)
async def process_comment(message: types.Message, state: FSMContext):
    comment = message.text.strip()
    await state.update_data(comment=comment if comment.lower() not in ("нет", "-", "no") else "—")

    data = await state.get_data()

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

    await message.answer(summary, parse_mode="HTML", reply_markup=confirm_kb())
    await state.set_state(BookingState.confirming)

# ═══════════════════════════════════════════════════════════════
# ПОДТВЕРЖДЕНИЕ ЗАЯВКИ
# ═══════════════════════════════════════════════════════════════

@dp.callback_query(BookingState.confirming, F.data == "confirm:yes")
async def confirm_booking(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user = callback.from_user

    admin_text = (
        f"🔔 <b>НОВАЯ ЗАЯВКА!</b>\n"
        f"{'═' * 30}\n\n"
        f"👤 <b>Клиент:</b> {data['name']}\n"
        f"📱 <b>Телефон:</b> <code>{data['phone']}</code>\n"
        f"📍 <b>Город:</b> {data['city']}\n"
        f"🆔 <b>Telegram:</b> @{user.username or 'нет username'}\n"
        f"🔗 <b>ID:</b> <code>{user.id}</code>\n\n"
        f"💄 <b>Услуга:</b> {data['service_name']}\n"
        f"💰 <b>Стоимость:</b> {data['service_price']}\n"
        f"💬 <b>Комментарий:</b> {data['comment']}\n\n"
        f"⏰ <b>Время заявки:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    try:
        await bot.send_message(
            ADMIN_ID,
            admin_text,
            parse_mode="HTML",
            reply_markup=admin_kb(user.id)
        )

        await callback.message.edit_text(
            "✅ <b>Заявка отправлена!</b>\n\n"
            f"Спасибо, {data['name']}! Наденька получила вашу заявку на <b>{data['service_name']}</b>.\n"
            f"Свяжется с вами в течение <b>2 часов</b> для согласования времени консультации.\n\n"
            f"📱 Ваш телефон: <code>{data['phone']}</code>\n"
            f"💰 К оплате: <b>{data['service_price']}</b>\n\n"
            f"Если есть срочные вопросы — пишите: @iwownadenka",
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(f"Ошибка отправки админу: {e}")
        await callback.message.edit_text(
            "⚠️ Произошла ошибка при отправке заявки. Пожалуйста, напишите напрямую: @iwownadenka",
            parse_mode="HTML"
        )

    await state.clear()
    await callback.answer()

@dp.callback_query(BookingState.confirming, F.data == "confirm:restart")
async def restart_booking(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Давайте начнём сначала! Выберите услугу:",
        reply_markup=main_menu_kb()
    )
    await callback.answer()

# ═══════════════════════════════════════════════════════════════
# АДМИН
# ═══════════════════════════════════════════════════════════════

@dp.callback_query(F.data.startswith("admin:accept:"))
async def admin_accept(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    user_id = int(callback.data.split(":")[2])

    try:
        await bot.send_message(
            user_id,
            "✅ <b>Ваша заявка принята!</b>\n\n"
            "Наденька свяжется с вами в ближайшее время для уточнения деталей и отправки ссылки на Zoom.\n"
            "Спасибо за доверие! 💕",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Не удалось уведомить клиента {user_id}: {e}")

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ <b>Заявка принята</b>",
        parse_mode="HTML"
    )
    await callback.answer("Клиент уведомлён")

# ═══════════════════════════════════════════════════════════════
# НЕИЗВЕСТНЫЕ СООБЩЕНИЯ
# ═══════════════════════════════════════════════════════════════

@dp.message()
async def unknown_message(message: types.Message, state: FSMContext):
    current_state = await state.get_state()

    if current_state is None:
        await message.answer(
            "Я не совсем понял 😊\n"
            "Давайте начнём с выбора услуги:",
            reply_markup=main_menu_kb()
        )

# ═══════════════════════════════════════════════════════════════
# ЗАПУСК
# ═══════════════════════════════════════════════════════════════

async def main():
    logger.info("🤖 Бот Future Mindset запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())