import os
import random
import pytz
from datetime import datetime, timedelta
from telegram import Bot, Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env файла
MONGO_URI = os.getenv("MONGO_URI")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not MONGO_URI or not BOT_TOKEN:
    print("Ошибка: Не найдены обязательные переменные окружения!")
    exit(1)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Проверка переменных окружения
MONGO_URI = os.getenv("MONGO_URI")  # URL подключения к MongoDB
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not MONGO_URI or not BOT_TOKEN:
    logger.error("Не найдены обязательные переменные окружения!")
    exit(1)

# Создание бота
bot = Bot(token=BOT_TOKEN)

# Обработчик команды /start
def start(update: Update, context: CallbackContext):
    """Отправляет приветственное сообщение и клавиатуру."""
    keyboard = [
        [KeyboardButton("Отправить начало тренировки")],
        [KeyboardButton("Отправить конец тренировки")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)

# Обработчик для кнопок "Отправить начало тренировки" и "Отправить конец тренировки"
def set_photo_type(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if update.message.text == "Отправить начало тренировки":
        context.user_data['photo_type'] = "start"
        update.message.reply_text("Теперь отправьте фото начала тренировки.")
    else:
        context.user_data['photo_type'] = "end"
        update.message.reply_text("Теперь отправьте фото конца тренировки.")

# Обработчик для получения фотографий
def handle_photo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    schedule = get_schedule()
    
    if user_id not in schedule:
        update.message.reply_text("Вы не зарегистрированы в системе.")
        return
    
    if 'photo_type' not in context.user_data:
        update.message.reply_text("Сначала выберите, какое фото хотите отправить.")
        return

    photo_type = context.user_data.pop('photo_type')  # Забираем и очищаем статус

    now = datetime.now(TZ)
    start_time = datetime.strptime(schedule[user_id]["start"], "%H:%M").time()
    end_time = datetime.strptime(schedule[user_id]["end"], "%H:%M").time()
    
    allowed_start = TZ.localize(datetime.combine(now.date(), start_time) - timedelta(minutes=10))
    allowed_end = TZ.localize(datetime.combine(now.date(), end_time) + timedelta(minutes=10))
    
    if photo_type == "start" and allowed_start <= now <= TZ.localize(datetime.combine(now.date(), start_time) + timedelta(minutes=10)):
        caption = get_random_text(TXT_START)
    elif photo_type == "end" and TZ.localize(datetime.combine(now.date(), end_time) - timedelta(minutes=10)) <= now <= allowed_end:
        caption = get_random_text(TXT_END)
    else:
        update.message.reply_text("Фотография отправлена не вовремя. Разрешается отправка за 10 минут до и в течение 10 минут после начала или конца тренировки")
        log_penalty(user_id)
        return
    
    channel_id = schedule[user_id]["channel"]
    bot.send_photo(chat_id=channel_id, photo=update.message.photo[-1].file_id, caption=caption)
    update.message.reply_text("Фото успешно отправлено!")

# Функция для получения расписания из базы данных MongoDB
def get_schedule():
    try:
        db = get_db_connection()
        if db is None:
            return {}
        
        schedule_collection = db.schedule  # Получаем коллекцию расписаний
        schedule_data = schedule_collection.find()  # Получаем все записи
        
        logger.debug("Расписание успешно получено из базы данных MongoDB.")
        return {str(row["_id"]): {"channel": row["channel_id"], "start": row["start_time"], "end": row["end_time"]} for row in schedule_data}
    except Exception as e:
        logger.error(f"Ошибка при получении расписания из базы данных MongoDB: {e}")
        return {}

# Подключение к базе данных MongoDB
def get_db_connection():
    """Создает и возвращает подключение к базе данных MongoDB."""
    try:
        client = MongoClient(MONGO_URI)
        db = client.get_database()  # Получаем базу данных
        logger.debug("Подключение к базе данных MongoDB успешно.")
        return db
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных MongoDB: {e}")
        return None

# Часовой пояс
TZ = pytz.timezone("Asia/Tashkent")

# Функция для отправки напоминания за 10 минут до начала тренировки
def send_reminder(context: CallbackContext):
    """Отправляет напоминание за 10 минут до начала тренировки."""
    schedule = get_schedule()
    now = datetime.now(TZ)

    for user_id, data in schedule.items():
        start_time = datetime.strptime(data["start"], "%H:%M").time()
        reminder_time = TZ.localize(datetime.combine(now.date(), start_time) - timedelta(minutes=10))

        if now >= reminder_time and now < reminder_time + timedelta(minutes=1):  # Проверяем, если сейчас время напоминания
            try:
                bot.send_message(
                    user_id,
                    "Скоро у вас начинается тренировка. Не забудьте отправить фото нажав на кнопку 'Отправить начало тренировки'."
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке напоминания тренеру {user_id}: {e}")

# Функция для проверки пропущенных отчетов
def check_missed_reports(context: CallbackContext):
    """Проверяет, кто не отправил фото вовремя, и уведомляет в общий чат."""
    schedule = get_schedule()
    now = datetime.now(TZ)
    for user_id, data in schedule.items():
        end_time = datetime.strptime(data["end"], "%H:%M").time()
        deadline = TZ.localize(datetime.combine(now.date(), end_time) + timedelta(minutes=10))
        
        if now > deadline:
            try:
                bot.send_message(CHAT_ID, f"<b>{user_id}</b>, вы не отправили фотоотчет вовремя!", parse_mode="HTML")
                log_penalty(user_id)
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления: {e}")

# Функция для записи штрафа в базу данных
def log_penalty(trainer_id):
    try:
        db = get_db_connection()
        if db is None:
            return
        penalties_collection = db.penalties  # Получаем коллекцию штрафов
        penalties_collection.insert_one({"trainer_id": trainer_id, "date": datetime.now(TZ)})
        logger.debug(f"Штраф для тренера {trainer_id} записан в базу данных MongoDB.")
    except Exception as e:
        logger.error(f"Ошибка при записи штрафа в базу данных MongoDB: {e}")

# Запуск бота
def main():
    """Запуск бота и планировщика."""
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Обработчики команд
    dispatcher.add_handler(CommandHandler("start", start))

    # Обработчик для кнопок
    dispatcher.add_handler(MessageHandler(Filters.text, set_photo_type))

    # Обработчик для получения фото
    dispatcher.add_handler(MessageHandler(Filters.photo, handle_photo))

    # Запуск напоминаний и проверки пропущенных отчетов
    updater.job_queue.run_repeating(send_reminder, interval=60, first=0)
    updater.job_queue.run_repeating(check_missed_reports, interval=60, first=0)

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
