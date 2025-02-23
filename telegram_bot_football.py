import logging
import json
from datetime import datetime, timedelta
from telegram import Update, Bot, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import os

# Установим логирование для ошибок
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальные переменные
bot = None
schedule_data = {}
photo_time_window = timedelta(minutes=10)
photo_channel = '@your_channel'  # Укажите канал, в который будете отправлять фото

# Загрузка расписания тренеров
def load_schedule():
    global schedule_data
    try:
        with open('schedule.json', 'r') as file:
            schedule_data = json.load(file)
    except Exception as e:
        logger.error(f"Ошибка при загрузке расписания: {e}")
        raise

# Чтение текста для начала и конца тренировки
def load_texts():
    try:
        with open('txt_start.txt', 'r') as file:
            start_text = file.read().strip()
        with open('txt_end.txt', 'r') as file:
            end_text = file.read().strip()
        return start_text, end_text
    except Exception as e:
        logger.error(f"Ошибка при загрузке текста: {e}")
        raise

start_text, end_text = load_texts()

# Функция приветствия
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Добро пожаловать в NOVA Assistant! Я буду помогать вам публиковать фотоотчеты ваших тренировок. Просто выберите нужную команду и отправьте одну фотографию начала или конца тренировки.",
        reply_markup=None
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Выберите команду:",
        reply_markup=ReplyKeyboardMarkup([["Отправить начало тренировки", "Отправить конец тренировки"]], one_time_keyboard=True)
    )

# Функция для получения и обработки фотографий
async def handle_photo(update: Update, context: CallbackContext) -> None:
    # Получаем данные тренера
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    photo = update.message.photo[-1].file_id

    # Определяем, что это за фотография
    if update.message.caption == "Отправить начало тренировки":
        action = "start"
    elif update.message.caption == "Отправить конец тренировки":
        action = "end"
    else:
        await update.message.reply_text("Ошибка: неправильная команда.")
        return

    # Проверяем время фотографии
    if not is_within_time_window(action):
        await update.message.reply_text("Фото отправлено в неподобающий момент. Пожалуйста, попробуйте снова.")
        return

    # Получаем текст и отправляем фото
    if action == "start":
        text_to_send = start_text
    elif action == "end":
        text_to_send = end_text

    try:
        # Публикуем фото
        await context.bot.send_photo(chat_id=photo_channel, photo=photo, caption=text_to_send)
        await update.message.reply_text("Фотография опубликована. Спасибо большое!")
    except Exception as e:
        logger.error(f"Ошибка при публикации фото: {e}")
        await update.message.reply_text("Ошибка при публикации фотографии. Пожалуйста, попробуйте снова.")

# Проверка, что фото отправлено в допустимое время
def is_within_time_window(action: str) -> bool:
    now = datetime.now()
    # Получаем информацию о тренировки
    schedule_info = get_schedule_for_user(user_id)
    training_start = schedule_info['start']
    training_end = schedule_info['end']

    # Проверяем, что фото отправлено в пределах 10 минут
    if action == "start" and (now - training_start).seconds <= photo_time_window.seconds:
        return True
    if action == "end" and (now - training_end).seconds <= photo_time_window.seconds:
        return True
    return False

# Функция для работы с расписанием
def get_schedule_for_user(user_id: int) -> dict:
    # Здесь будет код для извлечения информации о расписании из schedule.json
    # Для упрощения пока возвращаем фиктивные данные
    return {"start": datetime(2025, 2, 23, 10, 0), "end": datetime(2025, 2, 23, 11, 0)}

# Основная функция для запуска бота
async def main():
    application = Application.builder().token("YOUR_BOT_TOKEN").build()

    # Загрузка данных
    load_schedule()

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Запуск бота
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
