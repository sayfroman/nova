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

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Часовой пояс Ташкента
TASHKENT_TZ = pytz.timezone("Asia/Tashkent")

# Получение учетных данных Google
credentials_json = os.getenv("GOOGLE_CREDENTIALS")
if not credentials_json:
    logging.error("Переменная окружения GOOGLE_CREDENTIALS не установлена!")
    raise ValueError("Переменная GOOGLE_CREDENTIALS отсутствует!")

try:
    service_account_info = json.loads(credentials_json)
except json.JSONDecodeError as e:
    logging.error(f"Ошибка разбора JSON GOOGLE_CREDENTIALS: {e}")
    raise ValueError("Неверный формат JSON в GOOGLE_CREDENTIALS")

# Подключение к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(service_account_info, scopes=scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key("19vkwWg7jt6T5zjy9XpgYPQz0BA7mtfpSAt6s1hGA53g").sheet1

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

def get_schedule():
    try:
        data = sheet.get_all_records()
        return {str(row['Trainer_ID']): row for row in data}  # Приводим ID к строке
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}")
        return {}

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = ["5385649", "7368748440"]

TRAINER_KEYBOARD = ReplyKeyboardMarkup([
    ["Отправить начало тренировки"],
    ["Отправить конец тренировки"],
    ["Отправить фото"]
], resize_keyboard=True)

ADMIN_KEYBOARD = ReplyKeyboardMarkup([
    ["Опубликовать фото за тренера"],
    ["Посмотреть все штрафы"],
    ["Обратиться к тренеру"]
], resize_keyboard=True)

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

async def send_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    check_result = await check_training_time(user_id)
    if check_result is True:
        context.user_data['last_command'] = "start"
        await update.message.reply_text("Отправьте фото начала тренировки.")
    else:
        days, time, branch = check_result
        await update.message.reply_text(f"Сейчас не тренировочное время. Ваша ближайшая тренировка: {days} в {time}, филиал {branch}")

async def send_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    check_result = await check_training_time(user_id)
    if check_result is True:
        context.user_data['last_command'] = "end"
        await update.message.reply_text("Отправьте фото конца тренировки.")
    else:
        days, time, branch = check_result
        await update.message.reply_text(f"Сейчас не тренировочное время. Ваша ближайшая тренировка: {days} в {time}, филиал {branch}")

async def send_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    check_result = await check_training_time(user_id)
    if check_result is True:
        last_command = context.user_data.get('last_command')
        text = random.choice(START_TEXTS if last_command == "start" else END_TEXTS)
        await update.message.reply_text(f"Фото принято и отправлено. \n{text}")
    else:
        days, time, branch = check_result
        await update.message.reply_text(f"Сейчас не тренировочное время. Ваша ближайшая тренировка: {days} в {time}, филиал {branch}")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Regex("Отправить начало тренировки"), send_start))
app.add_handler(MessageHandler(filters.Regex("Отправить конец тренировки"), send_end))
app.add_handler(MessageHandler(filters.Regex("Отправить фото"), send_photo))

if __name__ == "__main__":
    logger.info("Запуск бота...")
    app.run_polling()


