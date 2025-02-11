import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from telegram.ext import MessageHandler, filters
from telegram.ext import CallbackContext

# Устанавливаем уровень логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Ваш токен
TOKEN = "7801498081:AAFCSe2aO5A2ZdnSqIblaf-45aRQQuybpqQ"

# Стартовая команда
async def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Отправить фотоотчет", callback_data='photo_report')],
        [InlineKeyboardButton("Посмотреть статистику штрафов", callback_data='view_fines')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Добро пожаловать! Выберите действие:', reply_markup=reply_markup)

# Обработка нажатий на кнопки
async def button(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    if query.data == 'photo_report':
        await query.edit_message_text(text="Пожалуйста, отправьте фотоотчет.")
        # Дополнительный код для обработки фотоотчетов

    elif query.data == 'view_fines':
        await query.edit_message_text(text="Показать статистику штрафов.")
        # Дополнительный код для статистики штрафов

# Обработка текста сообщений
async def handle_message(update: Update, context: CallbackContext):
    if update.message.text:
        text = update.message.text.lower()
        if 'фотоотчет' in text:
            # Дополнительная логика обработки фотоотчета
            await update.message.reply_text("Отправьте фото отчета.")
        elif 'штрафы' in text:
            # Логика для вывода статистики штрафов
            await update.message.reply_text("Показать статистику штрафов.")
        else:
            await update.message.reply_text("Не распознал команду. Пожалуйста, используйте кнопки.")

# Основная функция для запуска бота
async def main():
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()

    # Команды и обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
