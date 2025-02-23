import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import random
from datetime import datetime, timedelta
import pytz

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Тексты для начала и конца тренировки
start_texts = [
    "Тренировка началась! Удачи на поле! ⚽",
    "Время тренировки! Покажите свой лучший результат! 💪",
    "На старт, внимание, марш! 🏃‍♂️",
    "Тренировка стартовала! Пусть сегодня будет продуктивно! 🌟",
    "Поехали! Тренировка началась! 🚀"
]

end_texts = [
    "Тренировка завершена! Отличная работа! 👏",
    "Сегодня вы сделали большой шаг вперед! 🎉",
    "Тренировка окончена. Отдыхайте и восстанавливайтесь! 🌿",
    "Молодцы! Сегодня вы хорошо потрудились! 💯",
    "Тренировка завершена. До встречи на следующей! 👋"
]

# Расписание тренировок
schedule = [
    {
        "trainer_id": "6969603804",
        "name": "Бунед",
        "start": "17:00",
        "end": "18:00",
        "channel_id": "-1002331628469",
        "days": "Monday, Wednesday, Friday",
        "school": "Школа №295"
    },
    {
        "trainer_id": "413625395",
        "name": "Алексей",
        "start": "17:00",
        "end": "18:00",
        "channel_id": "-1002432571124",
        "days": "Monday, Wednesday, Friday",
        "school": "Школа №101"
    },
    {
        "trainer_id": "735570267",
        "name": "Марко",
        "start": "14:00",
        "end": "15:00",
        "channel_id": "-1002323472696",
        "days": "Monday, Wednesday, Friday",
        "school": "Школа №307"
    },
    {
        "trainer_id": "735570267",
        "name": "Марко",
        "start": "17:00",
        "end": "18:00",
        "channel_id": "-1002323472696",
        "days": "Monday, Wednesday, Friday",
        "school": "Школа №307"
    },
    {
        "trainer_id": "1532520919",
        "name": "Сардор",
        "start": "15:00",
        "end": "16:00",
        "channel_id": "-1002231891578",
        "days": "Monday, Wednesday, Friday",
        "school": "Школа №328"
    },
    {
        "trainer_id": "606134505",
        "name": "Миржалол",
        "start": "17:30",
        "end": "18:30",
        "channel_id": "-1002413556142",
        "days": "Tuesday, Thursday, Saturday",
        "school": "Школа №186"
    },
    {
        "trainer_id": "735570267",
        "name": "Марко",
        "start": "17:00",
        "end": "18:00",
        "channel_id": "-1002246173492",
        "days": "Tuesday, Thursday, Saturday",
        "school": "Школа №178"
    },
    {
        "trainer_id": "413625395",
        "name": "Алексей",
        "start": "15:00",
        "end": "16:00",
        "channel_id": "-1002460005367",
        "days": "Monday, Wednesday, Friday",
        "school": "Школа №254"
    },
    {
        "trainer_id": "6969603804",
        "name": "Бунед",
        "start": "15:00",
        "end": "16:00",
        "channel_id": "-1002344879265",
        "days": "Monday, Wednesday, Friday",
        "school": "Школа №117"
    },
    {
        "trainer_id": "7666290317",
        "name": "Адиба",
        "start": "14:00",
        "end": "15:00",
        "channel_id": "-1002309219325",
        "days": "Monday, Wednesday, Sunday",
        "school": "Школа №233"
    },
    {
        "trainer_id": "6969603804",
        "name": "Бунед",
        "start": "17:30",
        "end": "18:30",
        "channel_id": "-1002214695720",
        "days": "Tuesday, Thursday, Saturday",
        "school": "Школа №44"
    }
]

# Функция для получения текущего времени в Ташкенте
def get_current_time():
    return datetime.now(pytz.timezone('Asia/Tashkent'))

# Функция для отправки уведомлений за 10 минут до начала тренировки
async def send_notifications(context: ContextTypes.DEFAULT_TYPE):
    current_time = get_current_time()
    for session in schedule:
        start_time = datetime.strptime(session["start"], "%H:%M").time()
        notification_time = (datetime.combine(current_time.date(), start_time) - timedelta(minutes=10)).time()
        if current_time.time() >= notification_time and current_time.time() < start_time:
            if current_time.strftime("%A") in session["days"]:
                await context.bot.send_message(
                    chat_id=session["trainer_id"],
                    text=f"Тренировка скоро начинается. Не забудьте опубликовать фотоотчет."
                )

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    if any(session["trainer_id"] == user_id for session in schedule):
        reply_markup = ReplyKeyboardMarkup([["отправить начало тренировки", "отправить конец тренировки"]], resize_keyboard=True)
        await update.message.reply_text(
            "Добро пожаловать в NOVA Assistant. Я буду помогать вам публиковать фотоотчеты.",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Вы не зарегистрированы в системе.")

# Обработчик сообщений с фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    current_time = get_current_time()
    for session in schedule:
        if session["trainer_id"] == user_id and current_time.strftime("%A") in session["days"]:
            start_time = datetime.strptime(session["start"], "%H:%M").time()
            end_time = datetime.strptime(session["end"], "%H:%M").time()
            if current_time.time() >= start_time and current_time.time() <= end_time:
                try:
                    if update.message.text == "отправить начало тренировки":
                        caption = random.choice(start_texts)
                    elif update.message.text == "отправить конец тренировки":
                        caption = random.choice(end_texts)
                    else:
                        await update.message.reply_text("Неверная команда. Используйте кнопки.")
                        return

                    # Отправка фото в канал
                    await context.bot.send_photo(
                        chat_id=session["channel_id"],
                        photo=update.message.photo[-1].file_id,
                        caption=caption
                    )

                    # Уведомление об успешной публикации
                    await update.message.reply_text("Фотоотчет успешно отправлен!")
                except Exception as e:
                    # Уведомление об ошибке
                    logging.error(f"Ошибка при отправке фото: {e}")
                    await update.message.reply_text("Произошла ошибка при отправке фотоотчета. Пожалуйста, попробуйте еще раз.")
                return
    await update.message.reply_text("Сейчас не время для отправки фотоотчета.")

# Основная функция
def main():
    # Получаем токен из переменных окружения
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Токен бота не найден в переменных окружения!")

    application = ApplicationBuilder().token(token).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO & filters.TEXT, handle_photo))

    # Запуск уведомлений
    job_queue = application.job_queue
    job_queue.run_repeating(send_notifications, interval=60.0, first=0.0)

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
