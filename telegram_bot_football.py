import os
import json
import logging
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, JobQueue
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

def update_google_sheet_data(context: CallbackContext):
    global sheet
    try:
        sheet = gc.open_by_key("19vkwWg7jt6T5zjy9XpgYPQz0BA7mtfpSAt6s1hGA53g").sheet1
        logger.info("Данные из Google Sheets обновлены")
    except Exception as e:
        logger.error(f"Ошибка обновления Google Sheets: {e}")

# Получение токена бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [5385649, 7368748440]

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, JobQueue, CallbackQueryHandler
import datetime
import random

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
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if user_id in ADMIN_IDS:
        update.message.reply_text("Добро пожаловать, администратор!", reply_markup=ADMIN_KEYBOARD)
    else:
        update.message.reply_text(
            "Добро пожаловать в NOVA Assistant! Я буду помогать вам публиковать фотоотчеты ваших тренировок. "
            "Просто выберите нужную команду и отправьте одну фотографию начала или конца тренировки.",
            reply_markup=TRAINER_KEYBOARD
        )

# Получение расписания из Google Sheets
def get_schedule():
    try:
        data = sheet.get_all_records()
        return {row['Trainer_ID']: row for row in data}
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}")
        return {}

# Функция обработки фото
def handle_photo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    schedule = get_schedule()
    trainer_data = schedule.get(str(user_id))
    
    if not trainer_data:
        update.message.reply_text("Вы не зарегистрированы в системе.")
        return
    
    now = datetime.datetime.now(TASHKENT_TZ)
    start_time = datetime.datetime.strptime(trainer_data['Start_Time'], "%H:%M").time()
    end_time = datetime.datetime.strptime(trainer_data['End_Time'], "%H:%M").time()
    
    # Определение времени отправки
    if context.user_data.get("last_command") == "start":
        valid_from = (datetime.datetime.combine(now.date(), start_time) - datetime.timedelta(minutes=5)).time()
        valid_to = (datetime.datetime.combine(now.date(), start_time) + datetime.timedelta(minutes=12)).time()
    elif context.user_data.get("last_command") == "end":
        valid_from = (datetime.datetime.combine(now.date(), end_time) - datetime.timedelta(minutes=10)).time()
        valid_to = (datetime.datetime.combine(now.date(), end_time) + datetime.timedelta(minutes=12)).time()
    else:
        update.message.reply_text("Сначала выберите команду.")
        return
    
    if not (valid_from <= now.time() <= valid_to):
        update.message.reply_text("Фотография отправлена в неверное время.")
        return
    
    channel_id = trainer_data['Channel_ID']
    messages = ["Тренировка началась!", "Начинаем тренировку!", "Поехали!"] if context.user_data['last_command'] == "start" else ["Тренировка завершена!", "Конец тренировки!", "Финиш!"]
    caption = random.choice(messages)
    
    context.bot.send_photo(chat_id=channel_id, photo=update.message.photo[-1].file_id, caption=caption)
    update.message.reply_text("Фотография опубликована. Спасибо большое!")

# Функция для тренеров
def send_start(update: Update, context: CallbackContext):
    context.user_data['last_command'] = "start"
    update.message.reply_text("Отправьте фото начала тренировки.")

def send_end(update: Update, context: CallbackContext):
    context.user_data['last_command'] = "end"
    update.message.reply_text("Отправьте фото конца тренировки.")

# Функции для администраторов
def publish_for_trainer(update: Update, context: CallbackContext):
    update.message.reply_text("Выберите филиал:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(branch, callback_data=branch)] for branch in set(row['Branch'] for row in get_schedule().values())]))

def view_penalties(update: Update, context: CallbackContext):
    update.message.reply_text("Вывод информации о штрафах...")

def contact_trainer(update: Update, context: CallbackContext):
    update.message.reply_text("Выберите тренера:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(trainer['Trainer_Name'], callback_data=trainer['Trainer_ID'])] for trainer in get_schedule().values()]))

# Настройка команд
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Regex("Отправить начало тренировки"), send_start))
app.add_handler(MessageHandler(filters.Regex("Отправить конец тренировки"), send_end))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.Regex("Опубликовать фото за тренера"), publish_for_trainer))
app.add_handler(MessageHandler(filters.Regex("Посмотреть все штрафы"), view_penalties))
app.add_handler(MessageHandler(filters.Regex("Обратиться к тренеру"), contact_trainer))

# Запуск бота
app.run_polling()
