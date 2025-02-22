import os
import random
import pytz
import psycopg2
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor

DATABASE_URL = os.getenv("DATABASE_URL")
DB_CONNECTION = psycopg2.connect(DATABASE_URL)

TOKEN = os.getenv("BOT_TOKEN")
TZ = pytz.timezone("Asia/Tashkent")
CHAT_ID = "-4589851285"  # Общий чат для уведомлений
TXT_START = "txt_start.txt"  # Файл с текстами для начала тренировки
TXT_END = "txt_end.txt"  # Файл с текстами для конца тренировки

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Клавиатура с кнопками
start_end_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
start_end_keyboard.add(KeyboardButton("Отправить начало тренировки"))
start_end_keyboard.add(KeyboardButton("Отправить конец тренировки"))

trainer_state = {}  # Словарь для отслеживания статуса отправки фото тренером

def get_schedule():
    """Получает расписание из базы данных."""
    conn = DB_CONNECTION
    cursor = conn.cursor()
    cursor.execute("SELECT trainer_id, channel_id, start_time, end_time FROM \"NOVA-TABLE\"")
    data = cursor.fetchall()
    return {row[0]: {"channel": row[1], "start": row[2], "end": row[3]} for row in data}

def get_random_text(file_path):
    """Возвращает случайный текст из указанного TXT-файла."""
    with open(file_path, "r", encoding="utf-8") as file:
        texts = file.readlines()
    return random.choice(texts).strip()

def log_penalty(trainer_id):
    """Записывает штраф в базу данных."""
    conn = DB_CONNECTION
    cursor = conn.cursor()
    cursor.execute("INSERT INTO STRAFS (trainer_id, date) VALUES (%s, %s)", (trainer_id, datetime.now(TZ)))
    conn.commit()

@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await message.reply("Выберите действие:", reply_markup=start_end_keyboard)

@dp.message_handler(lambda message: message.text in ["Отправить начало тренировки", "Отправить конец тренировки"])
async def set_photo_type(message: types.Message):
    user_id = message.from_user.id
    if message.text == "Отправить начало тренировки":
        trainer_state[user_id] = "start"
        await message.reply("Теперь отправьте фото начала тренировки.")
    else:
        trainer_state[user_id] = "end"
        await message.reply("Теперь отправьте фото конца тренировки.")

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
    
    allowed_start = datetime.combine(now.date(), start_time) - timedelta(minutes=10)
    allowed_end = datetime.combine(now.date(), end_time) + timedelta(minutes=10)
    
    if photo_type == "start" and allowed_start <= now <= datetime.combine(now.date(), start_time) + timedelta(minutes=10):
        caption = get_random_text(TXT_START)
    elif photo_type == "end" and datetime.combine(now.date(), end_time) - timedelta(minutes=10) <= now <= allowed_end:
        caption = get_random_text(TXT_END)
    else:
        await message.reply("Фотография отправлена не вовремя. Разрешается отправка за 10 минут до и в течение 10 минут после начала или конца тренировки")
        log_penalty(user_id)
        return
    
    channel_id = schedule[user_id]["channel"]
    await bot.send_photo(chat_id=channel_id, photo=message.photo[-1].file_id, caption=caption)
    await message.reply("Фото успешно отправлено!")

async def check_missed_reports():
    """Проверяет, кто не отправил фото вовремя, и уведомляет в общий чат."""
    schedule = get_schedule()
    now = datetime.now(TZ)
    for user_id, data in schedule.items():
        end_time = datetime.strptime(data["end"], "%H:%M").time()
        deadline = datetime.combine(now.date(), end_time) + timedelta(minutes=10)
        
        if now > deadline:
            await bot.send_message(CHAT_ID, f"<b>{user_id}</b>, вы не отправили фотоотчет вовремя!", parse_mode="HTML")
            log_penalty(user_id)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
