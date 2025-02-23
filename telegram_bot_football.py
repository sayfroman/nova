import random
import pytz
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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

# Чат ID для уведомлений
CHAT_ID = "-4589851285"

# Файлы с текстами для начала и конца тренировки
TXT_START = "txt_start.txt"
TXT_END = "txt_end.txt"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot)  # Инициализация Dispatcher с передачей Bot через именованный аргумент

# Клавиатура с кнопками
start_end_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Отправить начало тренировки")],
        [KeyboardButton(text="Отправить конец тренировки")]
    ],
    resize_keyboard=True
)

trainer_state = {}  # Словарь для отслеживания статуса отправки фото тренером

# Функция для получения расписания из базы данных
def get_schedule():
    """Получает расписание из базы данных MongoDB."""
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

# Функция для загрузки данных в MongoDB
def load_schedule():
    """Загружает расписание в MongoDB."""
    try:
        db = get_db_connection()
        if db is None:
            return
        
        schedule_collection = db.schedule
        data = [
            {"trainer_id": "5212834409", "trainer_name": "Шохрух", "start_time": "17:00", "end_time": "18:00", "channel_id": "-1002331628469", "days_of_week": "Monday, Wednesday, Friday", "branch": "Школа №295"},
            {"trainer_id": "413625395", "trainer_name": "Алексей", "start_time": "17:00", "end_time": "18:00", "channel_id": "-1002432571124", "days_of_week": "Monday, Wednesday, Friday", "branch": "Школа №101"},
            {"trainer_id": "735570267", "trainer_name": "Марко", "start_time": "14:00", "end_time": "15:00", "channel_id": "-1002323472696", "days_of_week": "Monday, Wednesday, Friday", "branch": "Школа №307"},
            {"trainer_id": "735570267", "trainer_name": "Марко", "start_time": "17:00", "end_time": "18:00", "channel_id": "-1002323472696", "days_of_week": "Monday, Wednesday, Friday", "branch": "Школа №307"},
            {"trainer_id": "1532520919", "trainer_name": "Сардор", "start_time": "15:00", "end_time": "16:00", "channel_id": "-1002231891578", "days_of_week": "Monday, Wednesday, Friday", "branch": "Школа №328"},
            {"trainer_id": "606134505", "trainer_name": "Миржалол", "start_time": "17:30", "end_time": "18:30", "channel_id": "-1002413556142", "days_of_week": "Tuesday, Thursday, Saturday", "branch": "Школа №186"},
            {"trainer_id": "735570267", "trainer_name": "Марко", "start_time": "17:00", "end_time": "18:00", "channel_id": "-1002246173492", "days_of_week": "Tuesday, Thursday, Saturday", "branch": "Школа №178"},
            {"trainer_id": "413625395", "trainer_name": "Алексей", "start_time": "15:00", "end_time": "16:00", "channel_id": "-1002460005367", "days_of_week": "Monday, Wednesday, Friday", "branch": "Школа №254"},
            {"trainer_id": "6969603804", "trainer_name": "Бунед", "start_time": "15:00", "end_time": "16:00", "channel_id": "-1002344879265", "days_of_week": "Monday, Wednesday, Friday", "branch": "Школа №117"},
            {"trainer_id": "7666290317", "trainer_name": "Адиба", "start_time": "14:00", "end_time": "15:00", "channel_id": "-1002309219325", "days_of_week": "Monday, Wednesday, Sunday", "branch": "Школа №233"},
            {"trainer_id": "6969603804", "trainer_name": "Бунед", "start_time": "17:30", "end_time": "18:30", "channel_id": "-1002214695720", "days_of_week": "Tuesday, Thursday, Saturday", "branch": "Школа №44"}
        ]
        
        schedule_collection.insert_many(data)
        logger.debug("Данные расписания успешно загружены в базу данных MongoDB.")
    except Exception as e:
        logger.error(f"Ошибка при загрузке расписания в базу данных MongoDB: {e}")

# Логирование штрафа в базу данных
def log_penalty(trainer_id):
    """Записывает штраф в базу данных MongoDB."""
    try:
        db = get_db_connection()
        if db is None:
            return
        penalties_collection = db.penalties  # Получаем коллекцию штрафов
        penalties_collection.insert_one({"trainer_id": trainer_id, "date": datetime.now(TZ)})
        logger.debug(f"Штраф для тренера {trainer_id} записан в базу данных MongoDB.")
    except Exception as e:
        logger.error(f"Ошибка при записи штрафа в базу данных MongoDB: {e}")

# Обработчик команды "/start"
async def send_welcome(message: types.Message):
    await message.reply("Выберите действие:", reply_markup=start_end_keyboard)

dp.register_message_handler(send_welcome, commands=["start"])

# Обработчик для кнопок "Отправить начало тренировки" и "Отправить конец тренировки"
async def set_photo_type(message: types.Message):
    user_id = message.from_user.id
    if message.text == "Отправить начало тренировки":
        trainer_state[user_id] = "start"
        await message.reply("Теперь отправьте фото начала тренировки.")
    else:
        trainer_state[user_id] = "end"
        await message.reply("Теперь отправьте фото конца тренировки.")

dp.register_message_handler(set_photo_type, lambda message: message.text in ["Отправить начало тренировки", "Отправить конец тренировки"])

# Обработчик для получения фотографий
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    schedule = get_schedule()
    
    if user_id not in schedule:
        await message.reply("Вы не зарегистрированы в системе.")
        return
    
    if user_id not in trainer_state:
        await message.reply("Сначала выберите, какое фото хотите отправить.")
        return

    photo_type = trainer_state.pop(user_id)  # Забираем и очищаем статус

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
        await message.reply("Фотография отправлена не вовремя. Разрешается отправка за 10 минут до и в течение 10 минут после начала или конца тренировки")
        log_penalty(user_id)
        return
    
    channel_id = schedule[user_id]["channel"]
    await bot.send_photo(chat_id=channel_id, photo=message.photo[-1].file_id, caption=caption)
    await message.reply("Фото успешно отправлено!")

dp.register_message_handler(handle_photo, content_types=[types.ContentType.PHOTO])

# Функция для отправки напоминания за 10 минут до начала тренировки
async def send_reminder():
    """Отправляет напоминание за 10 минут до начала тренировки."""
    schedule = get_schedule()
    now = datetime.now(TZ)

    for user_id, data in schedule.items():
        start_time = datetime.strptime(data["start"], "%H:%M").time()
        reminder_time = TZ.localize(datetime.combine(now.date(), start_time) - timedelta(minutes=10))

        if now >= reminder_time and now < reminder_time + timedelta(minutes=1):  # Проверяем, если сейчас время напоминания
            try:
                await bot.send_message(
                    user_id,
                    "Скоро у вас начинается тренировка. Не забудьте отправить фото нажав на кнопку 'Отправить начало тренировки'."
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке напоминания тренеру {user_id}: {e}")

# Функция для проверки пропущенных отчетов
async def check_missed_reports():
    """Проверяет, кто не отправил фото вовремя, и уведомляет в общий чат."""
    schedule = get_schedule()
    now = datetime.now(TZ)
    for user_id, data in schedule.items():
        end_time = datetime.strptime(data["end"], "%H:%M").time()
        deadline = TZ.localize(datetime.combine(now.date(), end_time) + timedelta(minutes=10))
        
        if now > deadline:
            try:
                await bot.send_message(CHAT_ID, f"<b>{user_id}</b>, вы не отправили фотоотчет вовремя!", parse_mode="HTML")
                log_penalty(user_id)
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления: {e}")

# Создаем планировщик
scheduler = AsyncIOScheduler(timezone=TZ)

# Запускаем задачи
scheduler.add_job(send_reminder, "interval", minutes=1)
scheduler.add_job(check_missed_reports, "interval", minutes=1)
scheduler.start()

# Запускаем бота
async def main():
    try:
        load_schedule()
        await dp.start_polling()
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())
