import os
import json
import logging
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler, ContextTypes
import datetime
import random
import pytz

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

def get_schedule():
    try:
        data = sheet.get_all_records()
        if not data:
            logger.error("Google Sheets возвращает пустой список!")
        else:
            logger.info(f"Загружены данные: {data[:3]}")  # Показываем первые 3 записи
        return {str(row['Trainer_ID']): row for row in data}  # Приводим ID к строке
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}")
        return {}

def get_fines():
    try:
        fines_sheet = gc.open_by_key("19vkwWg7jt6T5zjy9XpgYPQz0BA7mtfpSAt6s1hGA53g").worksheet("Fines")
        data = fines_sheet.get_all_records()
        return data
    except Exception as e:
        logger.error(f"Ошибка загрузки штрафов: {e}")
        return []

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = ["5385649", "7368748440"]  # Приводим ID администраторов к строке

# Клавиатура для тренеров
TRAINER_KEYBOARD = ReplyKeyboardMarkup([
    ["Отправить начало тренировки"],
    ["Отправить конец тренировки"]
], resize_keyboard=True)

# Клавиатура для администраторов
ADMIN_KEYBOARD = ReplyKeyboardMarkup([
    ["Опубликовать фото за тренера"],
    ["Посмотреть все штрафы"],
    ["Обратиться к тренеру"]
], resize_keyboard=True)

# Приветствие тренера
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)  # Приводим user_id к строке
    schedule = get_schedule()
    
    logger.info(f"User ID: {user_id}")  # Логируем ID пользователя
    logger.info(f"Ключи в schedule: {list(schedule.keys())}")  # Логируем все Trainer_ID
    logger.info(f"Администраторы: {ADMIN_IDS}")  # Логируем список администраторов

    if user_id in ADMIN_IDS:
        await update.message.reply_text("Добро пожаловать, администратор!", reply_markup=ADMIN_KEYBOARD)
    elif user_id in schedule:
        await update.message.reply_text(
            "Добро пожаловать в NOVA Assistant! Я буду помогать вам публиковать фотоотчеты ваших тренировок. "
            "Просто выберите нужную команду и отправьте одну фотографию начала или конца тренировки.",
            reply_markup=TRAINER_KEYBOARD
        )
    else:
        await update.message.reply_text("Вы не зарегистрированы в системе. Обратитесь к администратору.")

async def send_fines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if user_id not in ADMIN_IDS:
        return
    
    fines = get_fines()
    if not fines:
        await update.message.reply_text("На данный момент штрафов нет.")
        return
    
    fines_by_trainer = {}
    for fine in fines:
        trainer_name = fine['Trainer_Name']
        date = fine['Date']
        time = fine['Time']
        if trainer_name not in fines_by_trainer:
            fines_by_trainer[trainer_name] = []
        fines_by_trainer[trainer_name].append(f"{date}, {time} — 1 штраф")
    
    message = "Статистика штрафов за текущий месяц:\n"
    for trainer, records in fines_by_trainer.items():
        message += f"\n🔹 {trainer}\n" + "\n".join(records) + "\n"
    
    await update.message.reply_text(message)

async def send_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['last_command'] = "start"
    await update.message.reply_text("Отправьте фото начала тренировки.")

async def send_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['last_command'] = "end"
    await update.message.reply_text("Отправьте фото конца тренировки.")

# Настройка команд
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stats", send_fines))
app.add_handler(MessageHandler(filters.Regex("Отправить начало тренировки"), send_start))
app.add_handler(MessageHandler(filters.Regex("Отправить конец тренировки"), send_end))

# Запуск бота
if __name__ == "__main__":
    logger.info("Запуск бота...")
    app.run_polling()

