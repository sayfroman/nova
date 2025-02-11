import pytz
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Устанавливаем временную зону для Ташкента
tashkent_tz = pytz.timezone('Asia/Tashkent')

# Получаем текущее время в Ташкенте
def get_current_time():
    now = datetime.now(tashkent_tz)
    return now

# Функция для проверки времени отправки фото
def check_photo_submission_time(training_start_time):
    current_time = get_current_time()  # Получаем текущее время в Ташкенте
    time_difference = current_time - training_start_time

    # Проверка на 12 минут после начала тренировки
    if time_difference > timedelta(minutes=12):
        return False  # Фото отправлено слишком поздно
    return True  # Фото отправлено вовремя

# Стартовый метод бота
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Здравствуйте! Я ваш бот для отправки фото отчетов.")

# Обработчик фото
async def handle_photo(update: Update, context: CallbackContext) -> None:
    # Получаем фото
    photo_file = update.message.photo[-1].get_file()
    photo_file.download('photo.jpg')

    # Время начала тренировки (пример)
    training_start_time = datetime(2025, 2, 11, 9, 0, 0, tzinfo=tashkent_tz)

    # Проверяем, отправлено ли фото вовремя
    if check_photo_submission_time(training_start_time):
        await update.message.reply_text("Фотография опубликована. Не забудьте также отправить фотографию об окончании тренировки.")
    else:
        await update.message.reply_text("Фотография отправлена слишком поздно и не принята. Вам начислен 1 штраф в виде 30% от оплаты за тренировку. Старайтесь отправлять фото вовремя.")

# Напоминания тренерам
async def send_reminders(context: CallbackContext):
    job = context.job
    bot = context.bot

    # Часы напоминаний
    reminder_time = get_current_time() + timedelta(hours=1)
    await bot.send_message(job.context['chat_id'], f"Через час у вас тренировка. Не забудьте отправить фотоотчеты вовремя.")

    # Напоминание в начале тренировки
    await bot.send_message(job.context['chat_id'], f"Тренировка началась. Не забудьте отправить фото 📸")

    # Напоминание об отправке фотографии после тренировки
    await bot.send_message(job.context['chat_id'], f"Фотография опубликована. Не забудьте также отправить фотографию об окончании тренировки")

# Старт планировщика для напоминаний
async def set_up_reminders(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    context.job_queue.run_once(send_reminders, 3600, context={'chat_id': chat_id})
    await update.message.reply_text("Напоминания установлены.")

# Функция для получения статистики штрафов
def get_fine_statistics():
    # Пример статистики
    fines_data = {
        "Иванов Иван": [
            {"date": "2 февраля", "time": "10:15", "fine": 1},
            {"date": "8 февраля", "time": "09:55", "fine": 1}
        ],
        "Петров Петр": [
            {"date": "5 февраля", "time": "11:20", "fine": 1}
        ]
    }

    statistics = "Статистика штрафов за февраль 2025:\n"
    for trainer, fines in fines_data.items():
        statistics += f"\n{trainer}\n"
        statistics += f"Количество штрафов: {len(fines)}\n"
        for fine in fines:
            statistics += f"{fine['date']}, {fine['time']} — {fine['fine']} штраф\n"
    return statistics

# Команда для получения статистики штрафов
async def fines(update: Update, context: CallbackContext):
    fines_data = get_fine_statistics()
    await update.message.reply_text(fines_data)

# Обработчик команд
async def main() -> None:
    # Настройка логирования
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Создаем объект бота
    bot = Bot("YOUR_BOT_API_KEY")
    application = Application.builder().token("7801498081:AAFCSe2aO5A2ZdnSqIblaf-45aRQQuybpqQ").build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("fines", fines))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CommandHandler("set_reminders", set_up_reminders))

    # Запуск бота
    await application.start_polling()

    # Работаем с напоминаниями
    application.job_queue.run_daily(send_reminders, time="09:00")

    # Ожидание работы бота
    await application.idle()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
