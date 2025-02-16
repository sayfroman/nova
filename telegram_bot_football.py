import os
import json
import logging
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ContextTypes
import datetime
import pytz
import random
import asyncio

# ==============================
# Настройка логирования
# ==============================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================
# Конфигурация часового пояса
# ==============================
TASHKENT_TZ = pytz.timezone("Asia/Tashkent")

# ==============================
# Подключение к Google Sheets
# ==============================
credentials_json = os.getenv("GOOGLE_CREDENTIALS")
if not credentials_json:
    logging.error("Переменная окружения GOOGLE_CREDENTIALS не установлена!")
    raise ValueError("Переменная GOOGLE_CREDENTIALS отсутствует!")

try:
    service_account_info = json.loads(credentials_json)
except json.JSONDecodeError as e:
    logging.error(f"Ошибка разбора JSON GOOGLE_CREDENTIALS: {e}")
    raise ValueError("Неверный формат JSON в GOOGLE_CREDENTIALS")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(service_account_info, scopes=scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key("19vkwWg7jt6T5zjy9XpgYPQz0BA7mtfpSAt6s1hGA53g").sheet1

# ==============================
# Текстовые шаблоны сообщений
# ==============================
START_TEXTS = [
    "Тренировка началась! Давайте покажем максимум! 💪⚽",
    "Начало тренировки! Готовимся к лучшим моментам! 🔥",
    "Стартуем! Сегодня мы станем сильнее! 🚀"
]

END_TEXTS = [
    "Тренировка завершена! Отличная работа, ребята! 👏",
    "Конец тренировки! Молодцы, продолжаем в том же духе! 🔥",
    "Завершили! Отличный результат, команда! 💯"
]

# ==============================
# Получение расписания из Google Sheets
# ==============================
def get_schedule():
    try:
        data = sheet.get_all_records()
        return {str(row['Trainer_ID']): row for row in data}  # Приводим ID к строке
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}")
        return {}

# ==============================
# Конфигурация бота
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = ["5385649", "7368748440"]

TRAINER_KEYBOARD = ReplyKeyboardMarkup([
    ["Отправить начало тренировки"],
    ["Отправить конец тренировки"],
    ["Мои штрафы"]
], resize_keyboard=True)

ADMIN_KEYBOARD = ReplyKeyboardMarkup([
    ["Опубликовать фото за тренера"],
    ["Посмотреть все штрафы"],
    ["Обратиться к тренеру"]
], resize_keyboard=True)

# ==============================
# Обработка команды /start
# ==============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    schedule = get_schedule()

    if user_id in ADMIN_IDS:
        await update.message.reply_text("Добро пожаловать, администратор!", reply_markup=ADMIN_KEYBOARD)
    elif user_id in schedule:
        await update.message.reply_text(
            "Добро пожаловать в NOVA Assistant! Выберите команду и отправьте фото начала или конца тренировки.",
            reply_markup=TRAINER_KEYBOARD
        )
    else:
        await update.message.reply_text("Вы не зарегистрированы в системе. Обратитесь к администратору.")

# ==============================
# Проверка времени тренировки
# ==============================
async def check_training_time(user_id: str):
    schedule = get_schedule()
    if user_id not in schedule:
        return None
    
    now = datetime.datetime.now(TASHKENT_TZ)
    user_schedule = schedule[user_id]
    training_days = user_schedule["Days_of_Week"].split(", ")
    today = now.strftime("%A")
    if today not in training_days:
        return None
    
    training_start = datetime.datetime.strptime(user_schedule["Start_Time"], "%H:%M").time()
    training_end = datetime.datetime.strptime(user_schedule["End_Time"], "%H:%M").time()
    if training_start <= now.time() <= training_end:
        return True
    return user_schedule["Days_of_Week"], user_schedule["Start_Time"], user_schedule["Branch"]

# ==============================
# Просмотр штрафов
# ==============================
async def view_fines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    fines_data = sheet.get_all_records()
    user_fines = next((row for row in fines_data if str(row['Trainer_ID']) == user_id), None)
    fines_count = user_fines['Fines'] if user_fines else 0
    
    if fines_count:
        await update.message.reply_text(f"В этом месяце у вас {fines_count} штраф(ов).")
    else:
        await update.message.reply_text("В текущем месяце штрафов нет.")

# ==============================
# Отправка напоминаний тренерам
# ==============================
async def send_reminders(app: Application):
    while True:
        schedule = get_schedule()
        now = datetime.datetime.now(TASHKENT_TZ)
        for user_id, details in schedule.items():
            training_start = datetime.datetime.strptime(details["Start_Time"], "%H:%M").time()
            training_end = datetime.datetime.strptime(details["End_Time"], "%H:%M").time()
            
            reminders = {
                (datetime.datetime.combine(now.date(), training_start) - datetime.timedelta(minutes=60)).time(): "До тренировки остался 1 час! ⏳",
                (datetime.datetime.combine(now.date(), training_start) - datetime.timedelta(minutes=30)).time(): "До тренировки осталось 30 минут! ⚽",
                (datetime.datetime.combine(now.date(), training_start) - datetime.timedelta(minutes=5)).time(): "Через 5 минут начнется тренировка! 📢",
                (datetime.datetime.combine(now.date(), training_end) - datetime.timedelta(minutes=10)).time(): "Тренировка заканчивается через 10 минут! 🕒"
            }
            
            if now.strftime("%A") in details["Days_of_Week"].split(", ") and now.time() in reminders:
                await app.bot.send_message(chat_id=user_id, text=reminders[now.time()])
        await asyncio.sleep(60)



