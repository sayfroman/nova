import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from datetime import datetime, timedelta
import pytz
import json

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("Ошибка: Не найден обязательный токен бота!")
    exit(1)

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Часовой пояс
TZ = pytz.timezone("Asia/Tashkent")

# Загружаем данные из файлов
def load_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logger.error(f"Ошибка загрузки данных из {filename}: {e}")
        return {}

def save_json(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Ошибка сохранения данных в {filename}: {e}")

# Пример структуры данных для schedule и penalties
schedule = load_json('schedule.json') or {}
penalties = load_json('penalties.json') or []

# Обработчик команды /start
async def start(update: Update, context: CallbackContext):
    """Отправляет приветственное сообщение и клавиатуру."""
    keyboard = [
        [KeyboardButton("Отправить начало тренировки")],
        [KeyboardButton("Отправить конец тренировки")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)

# Обработчик для кнопок "Отправить начало тренировки" и "Отправить конец тренировки"
async def set_photo_type(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if update.message.text == "Отправить начало тренировки":
        context.user_data['photo_type'] = "start"
        await update.message.reply_text("Теперь отправьте фото начала тренировки.")
    else:
        context.user_data['photo_type'] = "end"
        await update.message.reply_text("Теперь отправьте фото конца тренировки.")

# Обработчик для получения фотографий
async def handle_photo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id

    if str(user_id) not in schedule:
        await update.message.reply_text("Вы не зарегистрированы в системе.")
        return

    if 'photo_type' not in context.user_data:
        await update.message.reply_text("Сначала выберите, какое фото хотите отправить.")
        return

    photo_type = context.user_data.pop('photo_type')  # Забираем и очищаем статус

    now = datetime.now(TZ)
    start_time = datetime.strptime(schedule[str(user_id)]["start"], "%H:%M").time()
    end_time = datetime.strptime(schedule[str(user_id)]["end"], "%H:%M").time()

    allowed_start = TZ.localize(datetime.combine(now.date(), start_time) - timedelta(minutes=10))
    allowed_end = TZ.localize(datetime.combine(now.date(), end_time) + timedelta(minutes=10))

    if photo_type == "start" and allowed_start <= now <= TZ.localize(datetime.combine(now.date(), start_time) + timedelta(minutes=10)):
        caption = "Фото начала тренировки."
    elif photo_type == "end" and TZ.localize(datetime.combine(now.date(), end_time) - timedelta(minutes=10)) <= now <= allowed_end:
        caption = "Фото конца тренировки."
    else:
        await update.message.reply_text("Фотография отправлена не вовремя. Разрешается отправка за 10 минут до и в течение 10 минут после начала или конца тренировки")
        log_penalty(user_id)
        return

    channel_id = schedule[str(user_id)]["channel"]
    await update.message.reply_text(f"Фото отправлено в канал {channel_id}!")

# Функция для записи штрафа
def log_penalty(trainer_id):
    penalties.append({"trainer_id": trainer_id, "date": datetime.now(TZ).isoformat()})
    save_json('penalties.json', penalties)
    logger.debug(f"Штраф для тренера {trainer_id} записан.")

# Запуск бота
async def main():
    """Запуск бота и планировщика."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))

    # Обработчик для кнопок
    application.add_handler(MessageHandler(filters.TEXT, set_photo_type))

    # Обработчик для получения фото
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Запуск бота
    await application.run_polling()

if __name__ == "__main__":
    import asyncio

    # Проверка, работает ли уже цикл событий, и запуск бота
    if not asyncio.get_event_loop().is_running():
        asyncio.run(main())  # Запускаем асинхронную функцию main()
