# bot.py
import os
import telebot
from telebot import types
import re
import csv
import json
from datetime import datetime

# ====== Настройка токена ======
# Метод 1 (рекомендуется): передать переменную окружения BOT_TOKEN в настройках Bothost
TOKEN = os.environ.get("BOT_TOKEN", "").strip()

# Метод 2 (если не умеешь устанавливать переменные окружения) — прямо в код:
# TOKEN = "8583693802:AAEtK9dnCkEZDfqiF1u5FIN9CTbw57WEPv4"

if not TOKEN:
    raise SystemExit("8583693802:AAEtK9dnCkEZDfqiF1u5FIN9CTbw57WEPv4")

# ========== Параметры ==========
LEADS_FILE = "leads.csv"
STATE_FILE = "states.json"
OWNER_CHAT_ID = os.environ.get("OWNER_CHAT_ID")  # можно оставить пустым или задать как строку числа
# ===============================

bot = telebot.TeleBot(TOKEN)
EMAIL_RE = re.compile(r"^[^@ \t\r\n]+@[^@ \t\r\n]+\.[^@ \t\r\n]+$")
PHONE_RE = re.compile(r"^[\d\+\-\s\(\)]{6,20}$")

# загрузка состояний (чтобы не терять прогресс)
if os.path.exists(STATE_FILE):
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            STATES = json.load(f)
    except Exception:
        STATES = {}
else:
    STATES = {}

def save_states():
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(STATES, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Ошибка при сохранении states:", e)

def append_lead(record: dict):
    file_exists = os.path.exists(LEADS_FILE)
    with open(LEADS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "user_id", "username", "name", "email", "phone", "message"
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerow(record)

def make_main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(types.KeyboardButton("Пройти бриф"))
    kb.row(types.KeyboardButton("Отмена"))
    return kb

@bot.message_handler(commands=['start'])
def cmd_start(m: types.Message):
    text = (
        "Привет! 👋\n"
        "Я бот для короткого брифа — оставьте контакты и кратко опишите задачу.\n\n"
        "Нажмите «Пройти бриф» чтобы начать."
    )
    bot.send_message(m.chat.id, text, reply_markup=make_main_keyboard())

@bot.message_handler(commands=['help'])
def cmd_help(m: types.Message):
    bot.send_message(m.chat.id, "/start — начать\n/help — помощь\n/myid — показать ваш chat id (полезно владельцу)")

@bot.message_handler(commands=['myid'])
def cmd_myid(m: types.Message):
    bot.send_message(m.chat.id, f"Твой chat id: {m.chat.id}")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text(m: types.Message):
    user_id = str(m.chat.id)
    txt = m.text.strip()

    if txt.lower() == "отмена":
        if user_id in STATES:
            STATES.pop(user_id, None)
            save_states()
        bot.send_message(m.chat.id, "Отмена. Нажмите «Пройти бриф», чтобы начать снова.", reply_markup=make_main_keyboard())
        return

    if txt == "Пройти бриф":
        STATES[user_id] = {"step": "ask_name", "data": {}}
        save_states()
        bot.send_message(m.chat.id, "Как вас зовут?", reply_markup=types.ReplyKeyboardRemove())
        return

    state = STATES.get(user_id)
    if not state:
        bot.send_message(m.chat.id, "Нажмите «Пройти бриф», чтобы начать.", reply_markup=make_main_keyboard())
        return

    step = state.get("step")

    if step == "ask_name":
        state["data"]["name"] = txt
        state["step"] = "ask_email"
        save_states()
        bot.send_message(m.chat.id, "Укажите email или напишите «нет»:")
        return

    if step == "ask_email":
        if txt.lower() == "нет":
            state["data"]["email"] = ""
            state["step"] = "ask_phone"
            save_states()
            bot.send_message(m.chat.id, "Укажите телефон (например +7916...):")
            return
        if not EMAIL_RE.match(txt):
            bot.send_message(m.chat.id, "Похоже на неверный email. Попробуйте снова или напишите «нет».")
            return
        state["data"]["email"] = txt
        state["step"] = "ask_phone"
        save_states()
        bot.send_message(m.chat.id, "Спасибо. Теперь укажите телефон (или напишите «нет»):")
        return

    if step == "ask_phone":
        if txt.lower() == "нет":
            state["data"]["phone"] = ""
            state["step"] = "ask_message"
            save_states()
            bot.send_message(m.chat.id, "Кратко опишите задачу (1-2 предложения):")
            return
        if not PHONE_RE.match(txt):
            bot.send_message(m.chat.id, "Неверный формат телефона. Повторите или напишите «нет».")
            return
        state["data"]["phone"] = txt
        state["step"] = "ask_message"
        save_states()
        bot.send_message(m.chat.id, "Кратко опишите задачу (1-2 предложения):")
        return

    if step == "ask_message":
        state["data"]["message"] = txt
        d = state["data"]
        summary = (
            "Проверьте данные:\n\n"
            f"Имя: {d.get('name','')}\n"
            f"Email: {d.get('email','(не указан)')}\n"
            f"Телефон: {d.get('phone','(не указан)')}\n"
            f"Задача: {d.get('message','')}\n\n"
            "Если всё верно — напишите «Да». Чтобы отменить — «Отмена»."
        )
        state["step"] = "confirm"
        save_states()
        bot.send_message(m.chat.id, summary)
        return

    if step == "confirm":
        if txt.lower() in ("да", "ok", "подтвердить"):
            d = state["data"]
            record = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": m.chat.id,
                "username": (m.from_user.username or ""),
                "name": d.get("name",""),
                "email": d.get("email",""),
                "phone": d.get("phone",""),
                "message": d.get("message","")
            }
            try:
                append_lead(record)
            except Exception as e:
                bot.send_message(m.chat.id, "Ошибка при сохранении лида. Попробуйте позже.")
                print("Ошибка сохранения:", e)
                STATES.pop(user_id, None)
                save_states()
                return

            # уведомление владельца (если задан OWNER_CHAT_ID)
            try:
                if OWNER_CHAT_ID:
                    owner_id = int(OWNER_CHAT_ID)
                    owner_msg = (
                        "Новый лид:\n\n"
                        f"Имя: {record['name']}\n"
                        f"Email: {record['email'] or '(не указан)'}\n"
                        f"Телефон: {record['phone'] or '(не указан)'}\n"
                        f"Задача: {record['message']}\n"
                        f"Пользователь: @{record['username']} (id {record['user_id']})\n"
                        f"Время UTC: {record['timestamp']}"
                    )
                    bot.send_message(owner_id, owner_msg)
            except Exception as e:
                print("Не удалось отправить лид владельцу:", e)

            bot.send_message(m.chat.id, "Спасибо! Ваш бриф сохранён. Мы свяжемся с вами.", reply_markup=make_main_keyboard())
            STATES.pop(user_id, None)
            save_states()
            return
        else:
            bot.send_message(m.chat.id, "Если всё верно — напишите «Да». Или «Отмена» для отмены.")
            return

if __name__ == "__main__":
    print("Бот запущен.")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
