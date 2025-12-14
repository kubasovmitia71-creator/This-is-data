import telebot
from telebot import types
import json
from datetime import datetime
import os

# ================== НАСТРОЙКИ ==================

TOKEN = "8583693802:AAEtK9dnCkEZDfqiF1u5FIN9CTbw57WEPv4"
bot = telebot.TeleBot(TOKEN)

STATE_FILE = "states.json"
LEADS_FILE = "leads.json"

COVER_IMAGE_URL = "https://i.ibb.co/xSFNyQ3M/Screenshot-20251214-162350-cn-wps-moffice-i18n.png"

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
    chat_id = str(message.chat.id)

    states[chat_id] = {
        "step": STEP_ARTICLES,
        "data": {},
        "started_at": datetime.now().isoformat()
    }
    save_json(STATE_FILE, states)

    caption = (
        "👋 **Добро пожаловать!**\n\n"
        "Нажмите кнопку **СТАРТ**, чтобы получить полезные материалы\n"
        "и персональное предложение под ваш бизнес."
    )

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🚀 СТАРТ")

    bot.send_photo(
        message.chat.id,
        COVER_IMAGE_URL,
        caption=caption,
        parse_mode="Markdown",
        reply_markup=markup
    )

# ================== КНОПКА СТАРТ ==================

@bot.message_handler(func=lambda m: m.text == "🚀 СТАРТ")
def welcome(message):
    text = (
        "👋 **Приветствуем в боте This is data!**\n\n"
        "Я задам вам несколько коротких вопросов, чтобы:\n"
        "✅ рассчитать нагрузку на менеджеров\n"
        "✅ сделать для вас **лучшее предложение**\n\n"
        "📈 **Сейчас This is data — это:**\n"
        "✔️ 15+ активных клиентов\n"
        "✔️ 25 экспертов в команде\n"
        "✔️ +37% средний рост продаж\n"
        "✔️ 30% средняя маржинальность бизнеса клиентов"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )

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

# ================== ЛОГИКА ШАГОВ ==================

@bot.message_handler(func=lambda m: str(m.chat.id) in states and m.content_type == "text")
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
        bot.send_message(
            message.chat.id,
            "🧩 **В какой нише вы работаете?**",
            parse_mode="Markdown",
            reply_markup=types.ReplyKeyboardRemove()
        )

    elif step == STEP_NICHE:
        state["data"]["niche"] = text
        state["step"] = STEP_ARTICLE_WB
        save_json(STATE_FILE, states)
        bot.send_message(
            message.chat.id,
            "🏷 **Напишите любой артикул на WB**",
            parse_mode="Markdown"
        )

    elif step == STEP_ARTICLE_WB:
        state["data"]["wb_article"] = text
        state["step"] = STEP_PHONE
        save_json(STATE_FILE, states)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton(
                "📲 Поделиться номером",
                request_contact=True
            )
        )

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
    data["telegram"] = (
        f"@{message.from_user.username}"
        if message.from_user.username
        else "не указан"
    )
    data["date"] = datetime.now().isoformat()

    leads[chat_id] = data
    save_json(LEADS_FILE, leads)
    save_json(STATE_FILE, states)

    text = (
        "✅ **Спасибо за ответы!**\n\n"
        "Мы уже анализируем вашу ситуацию и подбираем\n"
        "**лучшие условия для сотрудничества** 💼\n\n"
        "🎁 **Ваши подарки:**\n"
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
