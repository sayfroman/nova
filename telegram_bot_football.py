import os
import json
import logging
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import datetime
import random

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
credentials = Credentials.from_service_account_info(service_account_info, scopes=scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key("19vkwWg7jt6T5zjy9XpgYPQz0BA7mtfpSAt6s1hGA53g").sheet1  # Укажите точное название таблицы

# Получаем токен бота из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [5385649, 7368748440]  # ID администраторов

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

# Функция для получения информации о тренере
def get_trainer_info(user_id):
    try:
        data = sheet.get_all_records()
        for row in data:
            if str(row["Trainer_ID"]) == str(user_id):
                return row["Branch"], row["Start_Time"], row["End_Time"], row["Channel_ID"], row["Days_of_Week"]
    except Exception as e:
        logging.error(f"Ошибка при получении данных из Google Sheets: {e}")
    return None, None, None, None, None

# Функция старта
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    
    # Проверка на авторизацию
    if user_id not in [trainer["Trainer_ID"] for trainer in sheet.get_all_records()]:
        await update.message.reply_text(
            "У вас нет доступа к использованию этого бота. Он создан только для тренерского штаба NOVA Football Uzbekistan. Обратитесь к руководству."
        )
        return

    # Вывод кнопок для тренера
    keyboard = [
        [InlineKeyboardButton("Отправить фото", callback_data="send_photo")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Выберите команду:", reply_markup=reply_markup)

# Функция для обработки фото
async def handle_photo(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    now = datetime.datetime.now().strftime("%H:%M")
    current_day = datetime.datetime.now().strftime("%A")  # Получаем день недели в формате "Monday"
    
    # Определяем день недели и расписание тренера
    branch, start_time, end_time, channel_id, days_of_week = get_trainer_info(user_id)
    if not branch:
        await update.message.reply_text("Вы не зарегистрированы как тренер!")
        return
    
    # Проверяем, что тренировка идет в правильный день недели
    days_of_week_list = [day.strip() for day in days_of_week.split(",")]  # Преобразуем строку в список дней
    if current_day not in days_of_week_list:
        await update.message.reply_text(f"У вас сегодня нет тренировок. Ваше расписание: {', '.join(days_of_week_list)}.")
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
    if update.message.photo:
        try:
            await context.bot.send_photo(chat_id=channel_id, photo=update.message.photo[-1].file_id, caption=message_text)
            await update.message.reply_text("Фото успешно опубликовано!")
        except Exception as e:
            logging.error(f"Ошибка при отправке фото: {e}")
            await update.message.reply_text("Ошибка при публикации фото. Попробуйте позже.")
    else:
        await update.message.reply_text("Фото не найдено!")

# Функция для проверки штрафов
async def penalties(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("У вас нет доступа к этой команде.")
        return
    
    report = "Статистика штрафов:\n"
    for trainer, count in PENALTIES.items():
        report += f"Тренер {trainer}: {count} штрафов\n"
    
    await update.message.reply_text(report)

# Функция для сброса штрафов
async def reset_penalties(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id not in ADMIN_IDS:
        await update.message.reply_text("У вас нет доступа к этой команде.")
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
