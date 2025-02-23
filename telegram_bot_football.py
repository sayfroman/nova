import os
import logging
from telegram import Update, Bot, ReplyKeyboardMarkup, KeyboardButton
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

# Создание бота
bot = Bot(token=BOT_TOKEN)

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
    await bot.send_photo(chat_id=channel_id, photo=update.message.photo[-1].file_id, caption=caption)
    await update.message.reply_text("Фото успешно отправлено!")

# Функция для записи штрафа
def log_penalty(trainer_id):
    penalties.append({"trainer_id": trainer_id, "date": datetime.now(TZ).isoformat()})
    save_json('penalties.json', penalties)
    logger.debug(f"Штраф для тренера {trainer_id} записан.")

# Функция для отправки напоминания за 10 минут до начала тренировки
async def send_reminder(context: CallbackContext):
    now = datetime.now(TZ)

    for user_id, data in schedule.items():
        start_time = datetime.strptime(data["start"], "%H:%M").time()
        reminder_time = TZ.localize(datetime.combine(now.date(), start_time) - timedelta(minutes=10))

        if now >= reminder_time and now < reminder_time + timedelta(minutes=1):
            try:
                await bot.send_message(
                    user_id,
                    "Скоро у вас начинается тренировка. Не забудьте отправить фото нажав на кнопку 'Отправить начало тренировки'."
                )
            except Exception as e:
                logger.error(f"Ошибка при отправке напоминания тренеру {user_id}: {e}")

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

    # Запуск напоминаний
    application.job_queue.run_repeating(send_reminder, interval=60, first=0)

    # Запуск бота
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())  # Запускаем асинхронную функцию main()
