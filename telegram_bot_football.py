import gspread
from google.oauth2.service_account import Credentials

# 1. Укажите путь к скачанному JSON-файлу
SERVICE_ACCOUNT_FILE = "solus-382301-5cbc0fd8d8cf.json"  # <-- Здесь впишите точное название вашего файла

# 2. Настроим доступ к Google Sheets API
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
client = gspread.authorize(creds)

# 3. Подключаем Google Таблицу по её ID
SPREADSHEET_ID = "19vkwWg7jt6T5zjy9XpgYPQz0BA7mtfpSAt6s1hGA53g"  # <-- Вставьте ID вашей таблицы сюда
sheet = client.open_by_key(SPREADSHEET_ID).sheet1  # Открываем первый лист

import logging
import random
import os
import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Настроим логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")  # ID администратора

# Пример данных тренеров и филиалов
TRAINERS = {
    "trainer_1": {"branch": "Branch_A", "start_time": "10:00", "end_time": "11:00"},
    "trainer_2": {"branch": "Branch_B", "start_time": "14:00", "end_time": "15:00"}
}

# Пример текстов для публикации
START_MESSAGES = [
    "Уважаемые родители, тренировка началась!",
    "Добрый день! Тренировка стартовала!",
    "Дети приступили к занятиям."
]
END_MESSAGES = [
    "Тренировка завершена, дети могут идти домой.",
    "Занятие окончено, ждем всех в следующий раз!",
    "Тренировка завершена. Хорошего вечера!"
]

# Хранение штрафов
PENALTIES = {}

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Привет! Отправляйте фотоотчет, и я опубликую его в нужном канале.")

async def handle_photo(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    now = datetime.datetime.now().strftime("%H:%M")
    
    # Определяем тренера и филиал
    trainer = None
    for t_id, data in TRAINERS.items():
        if str(user_id) == t_id:
            trainer = data
            break
    
    if not trainer:
        await update.message.reply_text("Вы не зарегистрированы как тренер!")
        return
    
    branch = trainer["branch"]
    start_time = trainer["start_time"]
    end_time = trainer["end_time"]
    
    # Проверяем время отправки фото
    if abs(int(now[:2]) * 60 + int(now[3:]) - int(start_time[:2]) * 60 - int(start_time[3:])) > 12:
        PENALTIES[user_id] = PENALTIES.get(user_id, 0) + 1
        await update.message.reply_text("Фото отправлено слишком поздно! Вам начислен штраф.")
        return
    
    # Выбираем случайное сообщение
    message_text = random.choice(START_MESSAGES if now <= end_time else END_MESSAGES)
    
    # Здесь должна быть отправка фото в нужный канал (замените CHANNEL_ID)
    CHANNEL_ID = "@your_channel_here"
    await context.bot.send_photo(chat_id=CHANNEL_ID, photo=update.message.photo[-1].file_id, caption=message_text)
    await update.message.reply_text("Фото успешно опубликовано!")

async def penalties(update: Update, context: CallbackContext) -> None:
    if str(update.message.from_user.id) != ADMIN_ID:
        return
    
    report = "Статистика штрафов:\n"
    for trainer, count in PENALTIES.items():
        report += f"Тренер {trainer}: {count} штрафов\n"
    
    await update.message.reply_text(report)

async def reset_penalties(update: Update, context: CallbackContext) -> None:
    if str(update.message.from_user.id) != ADMIN_ID:
        return
    
    PENALTIES.clear()
    await update.message.reply_text("Штрафы обнулены.")
# Проверяем подключение к Google Таблице
data = sheet.get_all_values()  # Считываем все данные из таблицы
print(data)  # Выводим их в консоль

# Запускаем бота
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CommandHandler("penalties", penalties))
    app.add_handler(CommandHandler("reset_penalties", reset_penalties))
    
    logger.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
