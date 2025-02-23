import os
import random
import pytz
import psycopg2
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Проверка переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not DATABASE_URL or not BOT_TOKEN:
    print("Не найдены обязательные переменные окружения!")
    exit(1)

# Подключение к базе данных
def get_db_connection():
    """Создает и возвращает подключение к базе данных."""
    try:
        return psycopg2.connect(DATABASE_URL)
    except Exception as e:
        print(f"Ошибка подключения к базе данных: {e}")
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
dp = Dispatcher()

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
    """Получает расписание из базы данных."""
    try:
        conn = get_db_connection()
        if conn is None:
            return {}
        
        cursor = conn.cursor()
        cursor.execute("SELECT trainer_id, channel_id, start_time, end_time FROM \"NOVA-TABLE\"")
        data = cursor.fetchall()
        conn.close()
        
        return {row[0]: {"channel": row[1], "start": row[2], "end": row[3]} for row in data}
    except Exception as e:
        print(f"Ошибка при получении расписания из базы данных: {e}")
        return {}

# Функция для получения случайного текста из файла
def get_random_text(file_path):
    """Возвращает случайный текст из указанного TXT-файла."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            texts = file.readlines()
        return random.choice(texts).strip()
    except Exception as e:
        print(f"Ошибка при чтении файла {file_path}: {e}")
        return "Ошибка при загрузке текста."

# Логирование штрафа в базу данных
def log_penalty(trainer_id):
    """Записывает штраф в базу данных."""
    try:
        conn = get_db_connection()
        if conn is None:
            return
        cursor = conn.cursor()
        cursor.execute("INSERT INTO STRAFS (trainer_id, date) VALUES (%s, %s)", (trainer_id, datetime.now(TZ)))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка при записи штрафа в базу данных: {e}")

# Обработчик команды "/start"
@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.reply("Выберите действие:", reply_markup=start_end_keyboard)

# Обработчик для кнопок "Отправить начало тренировки" и "Отправить конец тренировки"
@dp.message_handler(lambda message: message.text in ["Отправить начало тренировки", "Отправить конец тренировки"])
async def set_photo_type(message: types.Message):
    user_id = message.from_user.id
    if message.text == "Отправить начало тренировки":
        trainer_state[user_id] = "start"
        await message.reply("Теперь отправьте фото начала тренировки.")
    else:
        trainer_state[user_id] = "end"
        await message.reply("Теперь отправьте фото конца тренировки.")

# Обработчик для получения фотографий
@dp.message_handler(content_types=[types.ContentType.PHOTO])
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
                print(f"Ошибка при отправке напоминания тренеру {user_id}: {e}")

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
                print(f"Ошибка при отправке уведомления: {e}")

# Создаем планировщик
scheduler = AsyncIOScheduler()

# Добавляем задачи в планировщик
scheduler.add_job(send_reminder, 'interval', minutes=1)  # Проверка каждую минуту
scheduler.add_job(check_missed_reports, 'interval', minutes=5)  # Проверка пропущенных отчетов каждую 5 минуту

# Запуск планировщика и бота
async def on_start():
    scheduler.start()  # Запуск планировщика
    await dp.start_polling(skip_updates=True)  # Запуск бота без использования asyncio.run()

# Запуск планировщика и бота
if __name__ == "__main__":
    asyncio.run(on_start())
