import logging
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters

# Устанавливаем уровень логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Ваш токен
TOKEN = "7801498081:AAFCSe2aO5A2ZdnSqIblaf-45aRQQuybpqQ"

# Стартовая команда
async def start(update: Update, context: CallbackContext):
    keyboard = [
        ["Отправить фотоотчет"],
        ["Посмотреть статистику штрафов"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)

# Обработка сообщений
async def handle_message(update: Update, context: CallbackContext):
    text = update.message.text.lower()

    if "фотоотчет" in text:
        await update.message.reply_text("Пожалуйста, отправьте фотоотчет.")
    elif "штрафы" in text:
        await update.message.reply_text("Показать статистику штрафов.")
    else:
        await update.message.reply_text("Не распознал команду. Используйте кнопки.")

# Основная функция для запуска бота
async def main():
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота без asyncio.run()
    print("Бот запущен...")
    await application.run_polling()

# Исправленный запуск, который не вызывает ошибку в работающем event loop
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise e
