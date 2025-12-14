import os
import telebot
from telebot import types
import json
from datetime import datetime

# ================== НАСТРОЙКИ ==================

TOKEN = "8583693802:AAEtK9dnCkEZDfqiF1u5FIN9CTbw57WEPv4"

bot = telebot.TeleBot(TOKEN)

STATE_FILE = "states.json"
LEADS_FILE = "leads.json"

# 👉 ВСТАВЬ СЮДА СВОИ ССЫЛКИ
UNIT_ECONOMICS_LINK = "https://docs.google.com/spreadsheets/d/12zTHFASwrNlK8oUGVlODbrw7pmT7cg9RcobbTou9VQ8/edit?usp=sharing"
FIN_REPORT_LINK = "https://docs.google.com/spreadsheets/d/14AL1CU-qr6dj6_RdYnP9y8WUaCiB1mgNg8KKnfk8Nxo/edit?usp=sharing"

# ================== СОСТОЯНИЯ ==================

(
    STEP_ARTICLES,
    STEP_TURNOVER,
    STEP_NICHE,
    STEP_ARTICLE_WB,
    STEP_PHONE
) = range(5)

# ================== ХРАНЕНИЕ ==================

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

states = load_json(STATE_FILE)
leads = load_json(LEADS_FILE)

# ================== /START ==================

@bot.message_handler(commands=["start"])
def start(message):
    chat_id = message.chat.id

    states[str(chat_id)] = {
        "step": STEP_ARTICLES,
        "data": {},
        "started_at": datetime.now().isoformat()
    }
    save_json(STATE_FILE, states)

    text = (
        "🎁 **Подарок уже ждёт вас!**\n\n"
        "Я задам несколько коротких вопросов,\n"
        "чтобы:\n"
        "✅ мы могли расчитать нагрузку на наших менеджеров \n"
        "✅ подобрать для вас лучшее предложение\n\n"
        "⏱ Это займёт не больше 1 минуты"
    )

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚀 Начать")

    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

# ================== СТАРТ КНОПКОЙ ==================

@bot.message_handler(func=lambda m: m.text == "🚀 Начать")
def begin_questions(message):
    ask_articles(message.chat.id)

# ================== ВОПРОС 1 ==================

def ask_articles(chat_id):
    text = "📦 **Сколько у вас артикулов на Wildberries?**"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("До 30", "31–60")
    markup.add("61–100", "Больше 100")
    markup.add("✍️ Свой вариант")

    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

# ================== ВОПРОС 2 ==================

def ask_turnover(chat_id):
    text = "💰 **Средний оборот в месяц за последние 6 месяцев**"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("До 500 000 ₽")
    markup.add("500 000 – 1 500 000 ₽")
    markup.add("1 500 000 – 3 000 000 ₽")
    markup.add("Более 3 000 000 ₽")

    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)

# ================== ОБРАБОТКА ==================

@bot.message_handler(func=lambda m: str(m.chat.id) in states)
def handle_steps(message):
    chat_id = str(message.chat.id)
    state = states[chat_id]
    step = state["step"]
    text = message.text

    if step == STEP_ARTICLES:
        state["data"]["articles"] = text
        state["step"] = STEP_TURNOVER
        save_json(STATE_FILE, states)
        ask_turnover(message.chat.id)

    elif step == STEP_TURNOVER:
        state["data"]["turnover"] = text
        state["step"] = STEP_NICHE
        save_json(STATE_FILE, states)
        bot.send_message(message.chat.id,
            "🧩 **В какой нише вы работаете?**\n_(одежда, обувь, товары для дома и т.д.)_",
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardRemove()
        )

    elif step == STEP_NICHE:
        state["data"]["niche"] = text
        state["step"] = STEP_ARTICLE_WB
        save_json(STATE_FILE, states)
        bot.send_message(
            message.chat.id,
            "🏷 **Напишите любой из ваших артикулов на WB**\n_(достаточно одного)_",
            parse_mode="Markdown"
        )

    elif step == STEP_ARTICLE_WB:
        state["data"]["wb_article"] = text
        state["step"] = STEP_PHONE
        save_json(STATE_FILE, states)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("📲 Поделиться номером", request_contact=True))

        bot.send_message(
            message.chat.id,
            "📞 **Оставьте номер телефона для связи**",
            parse_mode="Markdown",
            reply_markup=markup
        )

# ================== КОНТАКТ ==================

@bot.message_handler(content_types=["contact"])
def handle_contact(message):
    chat_id = str(message.chat.id)

    if chat_id not in states:
        return

    state = states.pop(chat_id)
    data = state["data"]

    data["phone"] = message.contact.phone_number
    data["telegram"] = f"@{message.from_user.username}" if message.from_user.username else "не указан"
    data["date"] = datetime.now().isoformat()

    leads[chat_id] = data
    save_json(LEADS_FILE, leads)
    save_json(STATE_FILE, states)

    text = (
        "✅ **Спасибо!**\n\n"
        "Анализируем данные,\n"
        "**готовим предложение** 💼\n\n"
        "🎁 Забираейте бесплатные инструменты:\n"
        f"👉 <a href='{UNIT_ECONOMICS_LINK}'>Калькулятор юнит-экономики</a>\n"
        f"👉 <a href='{FIN_REPORT_LINK}'>Финансовый отчёт для WB</a>\n\n"
        "Мы скоро свяжемся с вами 📲"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove()
    )

# ================== ЗАПУСК ==================

bot.infinity_polling(skip_pending=True)
