import html
import json
import os
import random
from datetime import date

import telebot
from telebot import types

from config import TOKEN, ADMIN_ID

bot = telebot.TeleBot(TOKEN)
DB_FILE = "sparks.json"
LEADS_FILE = "leads.json"

LEGEND = (
    "📖 <b>Легенда Спарка</b>\n\n"
    "Давным-давно в серверной старого дата-центра случилось короткое замыкание. "
    "Все решили, что это поломка. Но из него родилась крошечная искра с "
    "собственным умом.\n\n"
    "Она сбежала по проводам в Telegram и теперь мечтает вырасти в настоящий огонь "
    "и осветить большой проект.\n\n"
    "Каждое твоё действие делает её ярче. Поможешь Спарку разгореться? 🔥"
)

ABOUT = (
    "ℹ️ <b>О боте</b>\n\n"
    "Spark — демо-бот. Он показывает, что умеют Telegram-боты:\n"
    "• меню с кнопками\n"
    "• хранение данных (искры, уровни, бонус дня)\n"
    "• приём заявок с пересылкой владельцу\n"
    "• мини-игры и случайные подборки\n\n"
    "Такого же бота можно сделать для вашего бизнеса: запись клиентов, "
    "прайс, ответы на частые вопросы, рассылки. "
    "Нажмите «Заказать бота», чтобы обсудить задачу."
)

IDEAS = [
    "Трекер привычек, который ругается, если ты пропустил день.",
    "Бот-напоминалка, которая сама подбирает смешные формулировки.",
    "Сайт-визитка для местной кофейни с онлайн-меню.",
    "Парсер скидок на любимые товары с уведомлением в Telegram.",
    "Бот для записи клиентов в барбершоп с напоминанием за час.",
    "Мини-игра «Угадай слово» прямо в Telegram.",
    "Бот-копилка: записывает траты и показывает статистику за неделю.",
]

TIPS = [
    "Читай сообщения об ошибках сверху вниз: причина обычно в последних строках.",
    "Делай маленькие шаги: запустил, проверил, добавил следующее.",
    "Называй переменные понятно: price лучше, чем p.",
    "Не храни пароли и токены в коде, который выкладываешь в интернет.",
    "Сломал код? Верни последнюю рабочую версию и попробуй иначе.",
    "Гугли ошибку целиком: кто-то уже с ней сталкивался.",
]

LEVELS = [
    (0, "Искорка"),
    (10, "Огонёк"),
    (30, "Пламя"),
    (60, "Костёр"),
    (100, "Маяк"),
]


# ---------- работа с файлами ----------

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_user(db, user_id):
    key = str(user_id)
    value = db.get(key, 0)
    if isinstance(value, int):  # старый формат: просто число искр
        value = {"sparks": value, "last_bonus": ""}
    db[key] = value
    return value


# ---------- искры и уровни ----------

def level_name(sparks):
    name = LEVELS[0][1]
    for need, title in LEVELS:
        if sparks >= need:
            name = title
    return name


def level_note(old_sparks, new_sparks):
    old_level = level_name(old_sparks)
    new_level = level_name(new_sparks)
    if new_level != old_level:
        return f"\n\n🎉 Новый уровень: <b>{new_level}</b>!"
    return ""


def add_sparks(user_id, amount=1):
    db = load_json(DB_FILE, {})
    user = get_user(db, user_id)
    old = user["sparks"]
    user["sparks"] += amount
    save_json(DB_FILE, db)
    return user["sparks"], level_note(old, user["sparks"])


def get_sparks(user_id):
    db = load_json(DB_FILE, {})
    return get_user(db, user_id)["sparks"]


def claim_bonus(user_id):
    db = load_json(DB_FILE, {})
    user = get_user(db, user_id)
    today = date.today().isoformat()
    if user["last_bonus"] == today:
        return None
    old = user["sparks"]
    user["last_bonus"] = today
    user["sparks"] += 3
    save_json(DB_FILE, db)
    return user["sparks"], level_note(old, user["sparks"])


# ---------- меню ----------

def menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✨ Идея дня", callback_data="idea"),
        types.InlineKeyboardButton("💡 Совет", callback_data="tip"),
        types.InlineKeyboardButton("🎲 Испытай удачу", callback_data="luck"),
        types.InlineKeyboardButton("🎁 Бонус дня", callback_data="bonus"),
        types.InlineKeyboardButton("🔥 Мой огонь", callback_data="me"),
        types.InlineKeyboardButton("📖 Легенда", callback_data="legend"),
        types.InlineKeyboardButton("🤖 Заказать бота", callback_data="order"),
        types.InlineKeyboardButton("ℹ️ Что это за бот", callback_data="about"),
    )
    return kb


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "⚡", reply_markup=types.ReplyKeyboardRemove())
    name = html.escape(message.from_user.first_name or "друг")
    bot.send_message(
        message.chat.id,
        f"⚡ <b>Пш-ш-ш...</b> Привет, {name}! Я Spark, демо-бот. "
        "Покажу, на что способны Telegram-боты.\n\nВыбери, что делать:",
        parse_mode="HTML",
        reply_markup=menu(),
    )


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(message.chat.id, ABOUT, parse_mode="HTML", reply_markup=menu())


@bot.callback_query_handler(func=lambda call: True)
def on_click(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    bot.answer_callback_query(call.id)

    if call.data == "idea":
        total, up = add_sparks(user_id)
        text = f"✨ <b>Идея дня:</b>\n{random.choice(IDEAS)}\n\n+1 искра (всего {total}){up}"
    elif call.data == "tip":
        total, up = add_sparks(user_id)
        text = f"💡 <b>Совет:</b>\n{random.choice(TIPS)}\n\n+1 искра (всего {total}){up}"
    elif call.data == "luck":
        roll = random.randint(1, 6)
        if roll == 6:
            total, up = add_sparks(user_id, 5)
            text = f"🎲 Выпало <b>{roll}</b>! Джекпот: +5 искр (всего {total}) 🎉{up}"
        else:
            total, up = add_sparks(user_id)
            text = f"🎲 Выпало <b>{roll}</b>. Утешительная +1 искра (всего {total}){up}"
    elif call.data == "bonus":
        result = claim_bonus(user_id)
        if result is None:
            text = "🎁 Бонус на сегодня уже получен. Возвращайся завтра!"
        else:
            total, up = result
            text = f"🎁 Бонус дня: +3 искры (всего {total}){up}"
    elif call.data == "me":
        total = get_sparks(user_id)
        text = (
            f"🔥 <b>Твой огонь</b>\nИскр: {total}\n"
            f"Уровень: <b>{level_name(total)}</b>"
        )
    elif call.data == "legend":
        text = LEGEND
    elif call.data == "about":
        text = ABOUT
    elif call.data == "order":
        msg = bot.send_message(
            chat_id,
            "🤖 Опиши, какой бот или программа тебе нужны. Я передам заявку разработчику:",
        )
        bot.register_next_step_handler(msg, receive_order)
        return
    else:
        return

    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=menu())


def receive_order(message):
    # если вместо описания пришла команда, отменяем заявку
    if message.text and message.text.startswith("/"):
        bot.send_message(
            message.chat.id,
            "Заявка отменена. Выбери, что делать:",
            reply_markup=menu(),
        )
        return

    task = message.text or "(без текста)"
    user = message.from_user

    leads = load_json(LEADS_FILE, [])
    leads.append(
        {
            "user_id": user.id,
            "name": user.first_name,
            "username": user.username,
            "task": task,
        }
    )
    save_json(LEADS_FILE, leads)

    if ADMIN_ID:
        try:
            bot.send_message(
                ADMIN_ID,
                f"📩 Новая заявка от {user.first_name} (@{user.username}):\n\n{task}",
            )
        except Exception as e:
            print("Не удалось отправить заявку владельцу:", e)

    bot.send_message(
        message.chat.id,
        "Заявка отправлена! Разработчик скоро свяжется с тобой ⚡",
        reply_markup=menu(),
    )


@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(
        message.chat.id,
        "Я понимаю только кнопки ⚡ Выбери действие в меню:",
        reply_markup=menu(),
    )


bot.infinity_polling()