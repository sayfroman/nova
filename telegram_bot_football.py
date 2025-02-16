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
# Проверка переменных окружения
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("Переменная BOT_TOKEN не установлена!")
    raise ValueError("Переменная BOT_TOKEN отсутствует!")

credentials_json = os.getenv("GOOGLE_CREDENTIALS")
if not credentials_json:
    logging.error("Переменная GOOGLE_CREDENTIALS не установлена!")
    raise ValueError("Переменная GOOGLE_CREDENTIALS отсутствует!")

# ==============================
# Подключение к Google Sheets
# ==============================
try:
    service_account_info = json.loads(credentials_json)
except json.JSONDecodeError as e:
    logging.error(f"Ошибка разбора JSON GOOGLE_CREDENTIALS: {e}")
    raise ValueError("Неверный формат JSON в GOOGLE_CREDENTIALS")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(service_account_info, scopes=scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key("19vkwWg7jt6T5zjy9XpgYPQz0BA7mtfpSAt6s1hGA53g").sheet1
fines_sheet = gc.open_by_key("19vkwWg7jt6T5zjy9XpgYPQz0BA7mtfpSAt6s1hGA53g").worksheet("Fines")

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

REMINDER_TEXTS = [
    "Напоминание: Ваша тренировка начинается через {minutes} минут! 🏆",
    "Скоро тренировка! Осталось {minutes} минут. Готовьтесь! ⚽",
    "Не забывайте: до начала вашей тренировки всего {minutes} минут! ⏳"
]

# ==============================
# Получение расписания из Google Sheets
# ==============================
def get_schedule():
    try:
        data = sheet.get_all_records()
        logging.info(f"Загружено расписание: {data}")
        return {str(row['Trainer_ID']): row for row in data}
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}")
        return {}

# ==============================
# Конфигурация бота
# ==============================
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
    try:
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
    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте снова позже.")

# ==============================
# Проверка времени тренировки
# ==============================
async def check_training_time(user_id: str):
    schedule = get_schedule()
    if user_id not in schedule:
        return None
    
    now = datetime.datetime.now(TASHKENT_TZ)
    user_schedule = schedule[user_id]
    training_start = datetime.datetime.strptime(user_schedule["Start_Time"], "%H:%M").time()
    training_end = datetime.datetime.strptime(user_schedule["End_Time"], "%H:%M").time()
    return training_start, training_end

# ==============================
# Фиксация штрафов
# ==============================
async def log_fine(user_id: str, reason: str):
    now = datetime.datetime.now(TASHKENT_TZ).strftime("%d-%m-%Y %H:%M")
    fines_sheet.append_row([user_id, reason, now])

# ==============================
# Обработка кнопки "Мои штрафы"
# ==============================
async def my_fines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.message.from_user.id)
        fines = fines_sheet.get_all_records()
        user_fines = [fine for fine in fines if fine["user_id"] == user_id]
        if user_fines:
            message = "Ваши штрафы:\n" + "\n".join([f"{fine['reason']} - {fine['date']}" for fine in user_fines])
        else:
            message = "У вас нет штрафов."
        await update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Ошибка при запросе штрафов: {e}")
        await update.message.reply_text("Ошибка при получении штрафов.")

# ==============================
# Обработка кнопки "Отправить начало тренировки"
# ==============================
async def send_start_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(random.choice(START_TEXTS))
    except Exception as e:
        logger.error(f"Ошибка при отправке начала тренировки: {e}")
        await update.message.reply_text("Ошибка при отправке начала тренировки.")

# ==============================
# Напоминания о тренировках
# ==============================
async def send_reminders():
    while True:
        schedule = get_schedule()
        now = datetime.datetime.now(TASHKENT_TZ).time()
        for user_id, user_schedule in schedule.items():
            training_start = datetime.datetime.strptime(user_schedule["Start_Time"], "%H:%M").time()
            for minutes in [60, 30, 5]:
                reminder_time = (datetime.datetime.combine(datetime.date.today(), training_start) - datetime.timedelta(minutes=minutes)).time()
                if now.hour == reminder_time.hour and now.minute == reminder_time.minute:
                    await app.bot.send_message(chat_id=user_id, text=random.choice(REMINDER_TEXTS).format(minutes=minutes))
        await asyncio.sleep(60)

# ==============================
# Регистрация команд бота
# ==============================
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Regex("Отправить начало тренировки"), send_start_training))
app.add_handler(MessageHandler(filters.Regex("Мои штрафы"), my_fines))
app.run_polling()



