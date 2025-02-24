import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext
import random
from datetime import datetime, timedelta
import pytz
import os

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
        "start": "01:00",
        "end": "02:00",
        "channel_id": "-1002309219325",
        "days": "Monday, Wednesday, Friday",
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

# Словарь для отслеживания отправленных уведомлений
notification_sent = {session["trainer_id"]: False for session in schedule}

# Функция для получения текущего времени в Ташкенте
def get_current_time():
    tz = pytz.timezone('Asia/Tashkent')
    return datetime.now(tz)

# Функция для отправки уведомлений за 10 минут до начала тренировки
async def send_notifications(context: CallbackContext):
    current_time = get_current_time()
    logging.info(f"Текущее время: {current_time}")

    for session in schedule:
        start_time = datetime.strptime(session["start"], "%H:%M").time()
        notification_time = (datetime.combine(current_time.date(), start_time) - timedelta(minutes=10)).time()
        
        logging.info(f"Время начала тренировки: {start_time}")
        logging.info(f"Время уведомления: {notification_time}")

        # Проверяем, что текущее время совпадает с временем уведомления
        if current_time.time() >= notification_time and current_time.time() < start_time:
            if current_time.strftime("%A") in session["days"]:
                # Проверяем, не было ли уже отправлено уведомление
                if not notification_sent[session["trainer_id"]]:
                    logging.info(f"Отправка уведомления тренеру {session['trainer_id']}")
                    try:
                        await context.bot.send_message(
                            chat_id=session["trainer_id"],
                            text=f"Тренировка скоро начинается. Не забудьте опубликовать фотоотчет."
                        )
                        # Помечаем уведомление как отправленное
                        notification_sent[session["trainer_id"]] = True
                    except Exception as e:
                        logging.error(f"Ошибка при отправке уведомления: {e}")
        else:
            # Сбрасываем флаг, если время уведомления прошло
            notification_sent[session["trainer_id"]] = False

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    logging.info(f"Получена команда /start от пользователя {user_id}")
    if any(session["trainer_id"] == user_id for session in schedule):
        reply_markup = ReplyKeyboardMarkup([["отправить начало тренировки", "отправить конец тренировки"]], resize_keyboard=True)
        await update.message.reply_text(
            "Добро пожаловать в NOVA Assistant. Я буду помогать вам публиковать фотоотчеты.",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("Вы не зарегистрированы в системе.")

# Обработчик нажатия на кнопки
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Пожалуйста, отправьте фотографию.")

# Обработчик сообщений с фото
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    current_time = get_current_time()
    logging.info(f"Получено фото от пользователя {user_id} в {current_time}")

    for session in schedule:
        if session["trainer_id"] == user_id and current_time.strftime("%A") in session["days"]:
            start_time = datetime.strptime(session["start"], "%H:%M").time()
            end_time = datetime.strptime(session["end"], "%H:%M").time()

            # Время для принятия фото начала тренировки: за 10 минут до начала и 15 минут после
            start_photo_start = (datetime.combine(current_time.date(), start_time) - timedelta(minutes=10)).time()
            start_photo_end = (datetime.combine(current_time.date(), start_time) + timedelta(minutes=15)).time()

            # Время для принятия фото конца тренировки: за 10 минут до конца и 15 минут после
            end_photo_start = (datetime.combine(current_time.date(), end_time) - timedelta(minutes=10)).time()
            end_photo_end = (datetime.combine(current_time.date(), end_time) + timedelta(minutes=15)).time()

            # Логирование для отладки
            logging.info(f"Текущее время: {current_time.time()}")
            logging.info(f"Время начала тренировки: {start_time}, Время окончания: {end_time}")
            logging.info(f"Диапазон для фото начала: {start_photo_start} - {start_photo_end}")
            logging.info(f"Диапазон для фото окончания: {end_photo_start} - {end_photo_end}")

            if update.message.text == "отправить начало тренировки":
                if start_photo_start <= current_time.time() <= start_photo_end:
                    try:
                        caption = random.choice(start_texts)
                        logging.info(f"Попытка отправить фото в канал {session['channel_id']}")
                        await context.bot.send_photo(
                            chat_id=session["channel_id"],
                            photo=update.message.photo[-1].file_id,
                            caption=caption
                        )
                        await update.message.reply_text("Фото успешно опубликовано!")
                    except Exception as e:
                        logging.error(f"Ошибка при отправке фото: {e}")
                        await update.message.reply_text("Фото не опубликовано, повторите заново, нажав /start")
                else:
                    await update.message.reply_text("Сейчас не время для фотоотчета. Проверьте свое расписание.")

            elif update.message.text == "отправить конец тренировки":
                if end_photo_start <= current_time.time() <= end_photo_end:
                    try:
                        caption = random.choice(end_texts)
                        logging.info(f"Попытка отправить фото в канал {session['channel_id']}")
                        await context.bot.send_photo(
                            chat_id=session["channel_id"],
                            photo=update.message.photo[-1].file_id,
                            caption=caption
                        )
                        await update.message.reply_text("Фото успешно опубликовано!")
                    except Exception as e:
                        logging.error(f"Ошибка при отправке фото: {e}")
                        await update.message.reply_text("Фото не опубликовано, повторите заново, нажав /start")
                else:
                    await update.message.reply_text("Сейчас не время для фотоотчета. Проверьте свое расписание.")
            return
    await update.message.reply_text("Вы не зарегистрированы в системе.")

# Основная функция
def main():
    # Получаем токен из переменных окружения
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Токен бота не найден в переменных окружения!")

    # Создаем приложение
    application = ApplicationBuilder().token(token).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))  # Измененный фильтр

    # Настройка вебхука
    webhook_url = os.getenv("WEBHOOK_URL")  # URL вашего бота на Railway
    if not webhook_url:
        raise ValueError("WEBHOOK_URL не найден в переменных окружения!")

    # Запуск планировщика для уведомлений
    job_queue = application.job_queue
    job_queue.run_repeating(send_notifications, interval=60.0, first=0.0)  # Проверка каждую минуту

    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 8443)),
        webhook_url=webhook_url,
        url_path=token,
    )

if __name__ == "__main__":
    main()
