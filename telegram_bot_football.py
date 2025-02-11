import os
import json
import logging
import random
import datetime
gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем учетные данные Google из переменной окружения
credentials_json = os.getenv("GOOGLE_CREDENTIALS")
if not credentials_json:
    logging.error("Переменная окружения GOOGLE_CREDENTIALS не установлена или пуста!")
    raise ValueError("GOOGLE_CREDENTIALS environment variable is missing or empty")

try:
    service_account_info = json.loads(credentials_json)
except json.JSONDecodeError as e:
    logging.error(f"Ошибка при разборе JSON GOOGLE_CREDENTIALS: {e}")
    raise ValueError("Invalid JSON format in GOOGLE_CREDENTIALS")

# Подключаемся к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
gc = gspread.authorize(credentials)
sheet = gc.open("Football_Schedule").sheet1  # Укажите точное название таблицы

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # Приводим к числу

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

def get_trainer_info(user_id):
    try:
        data = sheet.get_all_records()
        for row in data:
            if str(row["Trainer_ID"]) == str(user_id):
                return row["Branch"], row["Start_Time"], row["End_Time"]
    except Exception as e:
        logging.error(f"Ошибка при получении данных из Google Sheets: {e}")
    return None, None, None

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Привет! Отправляйте фотоотчет, и я опубликую его в нужном канале.")

async def handle_photo(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    now = datetime.datetime.now().strftime("%H:%M")
    
    # Определяем филиал и расписание тренера
    branch, start_time, end_time = get_trainer_info(user_id)
    if not branch:
        await update.message.reply_text("Вы не зарегистрированы как тренер!")
        return
    
    # Проверяем время отправки фото
    time_now = datetime.datetime.strptime(now, "%H:%M").time()
    start_dt = datetime.datetime.strptime(start_time, "%H:%M").time()
    end_dt = datetime.datetime.strptime(end_time, "%H:%M").time()
    
    if abs((datetime.datetime.combine(datetime.date.today(), time_now) - 
            datetime.datetime.combine(datetime.date.today(), start_dt)).total_seconds()) > 720:
        PENALTIES[user_id] = PENALTIES.get(user_id, 0) + 1
        await update.message.reply_text("Фото отправлено слишком поздно! Вам начислен штраф.")
        return
    
    # Выбираем случайное сообщение
    message_text = random.choice(START_MESSAGES if time_now <= end_dt else END_MESSAGES)
    
    # Отправляем фото в канал
    CHANNEL_ID = "@your_channel_here"
    try:
        await context.bot.send_photo(chat_id=CHANNEL_ID, photo=update.message.photo[-1].file_id, caption=message_text)
        await update.message.reply_text("Фото успешно опубликовано!")
    except Exception as e:
        logging.error(f"Ошибка при отправке фото: {e}")
        await update.message.reply_text("Ошибка при публикации фото. Попробуйте позже.")

async def penalties(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != ADMIN_ID:
        return
    
    report = "Статистика штрафов:\n"
    for trainer, count in PENALTIES.items():
        report += f"Тренер {trainer}: {count} штрафов\n"
    
    await update.message.reply_text(report)

async def reset_penalties(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != ADMIN_ID:
        return
    
    PENALTIES.clear()
    await update.message.reply_text("Штрафы обнулены.")

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
