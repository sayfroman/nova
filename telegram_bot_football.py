import os
import json
import logging
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import datetime
import random
import pytz

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Часовой пояс Ташкента
TASHKENT_TZ = pytz.timezone("Asia/Tashkent")

# Получение учетных данных Google
credentials_json = os.getenv("GOOGLE_CREDENTIALS")
if not credentials_json:
    logging.error("Переменная окружения GOOGLE_CREDENTIALS не установлена!")
    raise ValueError("Переменная GOOGLE_CREDENTIALS отсутствует!")

try:
    service_account_info = json.loads(credentials_json)
except json.JSONDecodeError as e:
    logging.error(f"Ошибка разбора JSON GOOGLE_CREDENTIALS: {e}")
    raise ValueError("Неверный формат JSON в GOOGLE_CREDENTIALS")

# Подключение к Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(service_account_info, scopes=scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key("1aBcDeFgHiJkLmNOpQrStUvWxYz").sheet1  # Используем ID таблицы

# Получение токена бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [5385649, 7368748440]

# Примеры сообщений
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

# Получение данных тренера
def get_trainer_info(user_id):
    try:
        data = sheet.get_all_records()
        for row in data:
            if "Trainer_ID" in row and str(row["Trainer_ID"]) == str(user_id):
                return row["Branch"], row["Start_Time"], row["End_Time"], row["Channel_ID"], row.get("Days_of_Week", "")
    except Exception as e:
        logging.error(f"Ошибка при получении данных из Google Sheets: {e}")
    return None, None, None, None, None

# Команда /start
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    data = sheet.get_all_records()
    
    if not any(str(row.get("Trainer_ID", "")) == str(user_id) for row in data):
        await update.message.reply_text(
            "Простите, но у вас нет доступа. Бот создан только для тренерского штаба NOVA Football Uzbekistan."
        )
        return

    keyboard = [[InlineKeyboardButton("Отправить фото", callback_data="send_photo")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Выберите команду:", reply_markup=reply_markup)

# Обработка фото
async def handle_photo(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    now = datetime.datetime.now(TASHKENT_TZ).time()
    current_day = datetime.datetime.now(TASHKENT_TZ).strftime("%A")
    
    branch, start_time, end_time, channel_id, days_of_week = get_trainer_info(user_id)
    if not branch:
        await update.message.reply_text("Вы не зарегистрированы как тренер!")
        return
    
    if not days_of_week:
        await update.message.reply_text("Ошибка в данных: отсутствует информация о днях тренировок.")
        return

    days_of_week_list = [day.strip() for day in days_of_week.split(",")]
    if current_day not in days_of_week_list:
        await update.message.reply_text(f"Сегодня нет тренировки. Ваши дни: {', '.join(days_of_week_list)}.")
        return
    
    try:
        start_dt = datetime.datetime.strptime(start_time, "%H:%M").time()
        end_dt = datetime.datetime.strptime(end_time, "%H:%M").time()
    except ValueError:
        await update.message.reply_text("Ошибка в данных расписания. Проверьте Google Таблицу.")
        return

    # Проверка штрафов
    time_difference_start = abs((datetime.datetime.combine(datetime.date.today(), now) - 
                                 datetime.datetime.combine(datetime.date.today(), start_dt)).total_seconds())
    
    time_difference_end = abs((datetime.datetime.combine(datetime.date.today(), now) - 
                               datetime.datetime.combine(datetime.date.today(), end_dt)).total_seconds())

    if time_difference_start > 720 and time_difference_end > 720:
        PENALTIES[user_id] = PENALTIES.get(user_id, 0) + 1
        await update.message.reply_text("Фото отправлено слишком поздно! Вам начислен штраф.")
        return

    # Выбор сообщения
    if time_difference_start <= 720:
        message_text = random.choice(START_MESSAGES)
    elif time_difference_end <= 720:
        message_text = random.choice(END_MESSAGES)
    else:
        message_text = "Фото получено, но не соответствует времени тренировки."

    # Отправка фото
    if update.message.photo:
        try:
            await context.bot.send_photo(chat_id=channel_id, photo=update.message.photo[-1].file_id, caption=message_text)
            await update.message.reply_text("Фото успешно опубликовано!")
        except Exception as e:
            logging.error(f"Ошибка отправки фото: {e}")
            await update.message.reply_text("Ошибка при публикации. Попробуйте позже.")
    else:
        await update.message.reply_text("Фото не обнаружено!")

# Запуск бота
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    logger.info("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
