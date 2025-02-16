# Импорт необходимых библиотек
import os
import json
import logging
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, JobQueue
import datetime
import random
import pytz

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Часовой пояс Ташкента
TASHKENT_TZ = pytz.timezone("Asia/Tashkent")

# Получение учетных данных Google
# Эта часть кода отвечает за получение учетных данных для доступа к Google Sheets
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
# Подключение к Google Sheets с использованием полученных учетных данных
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(service_account_info, scopes=scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key("19vkwWg7jt6T5zjy9XpgYPQz0BA7mtfpSAt6s1hGA53g").sheet1

# Функция обновления данных из Google Sheets
# Эта функция обновляет данные из Google Sheets каждые 5 минут
def update_google_sheet_data(context: CallbackContext):
    global sheet
    try:
        sheet = gc.open_by_key("19vkwWg7jt6T5zjy9XpgYPQz0BA7mtfpSAt6s1hGA53g").sheet1
        logger.info("Данные из Google Sheets обновлены")
    except Exception as e:
        logger.error(f"Ошибка обновления Google Sheets: {e}")

# Получение токена бота и настроек
# Здесь находятся настройки бота, такие как токен и ID администраторов
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = ["5385649", "7368748440"]

# Примеры сообщений
# Сообщения, которые будут отправляться при начале и окончании тренировки
START_MESSAGES = [
    """🏆 Тренировка началась! Команда уже на поле!
    🏆 Mashg’ulot boshlandi! Jamoa maydonda!""",
]

END_MESSAGES = [
    """✅ Тренировка окончена! Все отлично потрудились!
    ✅ Mashg‘ulot tugadi! Hammasi zo‘r ishladi!""",
]

# Хранение штрафов
# Здесь будет храниться информация о штрафах тренеров
PENALTIES = {}

# Функция получения данных тренера
# Эта функция получает информацию о тренере из Google Sheets
def get_trainer_info(user_id):
    try:
        data = sheet.get_all_records()
        trainer_sessions = []
        for row in data:
            if "Trainer_ID" in row and str(row["Trainer_ID"]) == str(user_id):
                trainer_sessions.append({
                    "branch": row["Branch"],
                    "start_time": row["Start_Time"],
                    "end_time": row["End_Time"],
                    "channel_id": row["Channel_ID"],
                    "days_of_week": row.get("Days_of_Week", ""),
                    "trainer_name": row.get("Trainer_Name", "Тренер")
                })
        return trainer_sessions
    except Exception as e:
        logging.error(f"Ошибка при получении данных из Google Sheets: {e}")
    return []

# Команда /start
# Обработчик команды /start, который приветствует тренера
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    data = sheet.get_all_records()
    
    trainer_name = "Тренер"
    for row in data:
        if str(row.get("Trainer_ID", "")) == str(user_id):
            trainer_name = row.get("Trainer_Name", "Тренер")
            break
    
    if not any(str(row.get("Trainer_ID", "")) == str(user_id) for row in data):
        await update.message.reply_text(
            "Простите, но у вас нет доступа. Бот создан только для тренерского штаба NOVA Football Uzbekistan."
        )
        return

    keyboard = [["Отправить фото"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(f"Привет, {trainer_name}! Выберите команду:", reply_markup=reply_markup)

# Обработчик нажатия на кнопку "Отправить фото"
# Этот обработчик запрашивает фото от тренера
async def handle_photo_request(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Пожалуйста, отправьте фото для отчета.")

# Обработка фото
# Обработчик, который проверяет время тренировки и отправляет фото в канал
async def handle_photo(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    now = datetime.datetime.now(TASHKENT_TZ).time()
    current_day = datetime.datetime.now(TASHKENT_TZ).strftime("%A")
    
    # Проверка, отправляется ли фото в альбоме
    if update.message.media_group_id:
        await update.message.reply_text("Пожалуйста, отправьте фото отдельным сообщением, а не альбом.")
        return
    
    trainer_sessions = get_trainer_info(user_id)
    if not trainer_sessions:
        await update.message.reply_text("Вы не зарегистрированы как тренер!")
        return
    
    for session in trainer_sessions:
        days_of_week_list = [day.strip() for day in session["days_of_week"].split(",")]
        if current_day not in days_of_week_list:
            continue
        
        try:
            start_dt = datetime.datetime.strptime(session["start_time"], "%H:%M").time()
            end_dt = datetime.datetime.strptime(session["end_time"], "%H:%M").time()
        except ValueError:
            continue
        
        start_early = (datetime.datetime.combine(datetime.date.today(), start_dt) - datetime.timedelta(minutes=5)).time()
        start_late = (datetime.datetime.combine(datetime.date.today(), start_dt) + datetime.timedelta(minutes=12)).time()
        end_early = (datetime.datetime.combine(datetime.date.today(), end_dt) - datetime.timedelta(minutes=12)).time()
        end_late = (datetime.datetime.combine(datetime.date.today(), end_dt) + datetime.timedelta(minutes=12)).time()
        
        # Фотография начала тренировки
        if start_early <= now <= start_late:
            if update.message.photo:
                try:
                    if f'start_photo_sent_{user_id}' not in context.chat_data:
                        await context.bot.send_photo(chat_id=session["channel_id"], photo=update.message.photo[-1].file_id, caption=random.choice(START_MESSAGES))
                        context.chat_data[f'start_photo_sent_{user_id}'] = True
                        await update.message.reply_text(f"{session['trainer_name']}, фото начала тренировки отправлено! Нажмите кнопку ниже для отправки фото окончания тренировки.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Отправить конечное фото", callback_data="send_end_photo")]]))
                        return
                    else:
                        await update.message.reply_text("Нужна только одна фотография. Все остальные записи с тренировки отправляйте менеджеру в чат.")
                except Exception as e:
                    logging.error(f"Ошибка отправки фото: {e}")
                    await update.message.reply_text("Ошибка при публикации. Попробуйте позже.")
                    return
        
        # Фотография конца тренировки
        if end_early <= now <= end_late:
            if update.message.photo:
                try:
                    if f'end_photo_sent_{user_id}' not in context.chat_data:
                        await context.bot.send_photo(chat_id=session["channel_id"], photo=update.message.photo[-1].file_id, caption=random.choice(END_MESSAGES))
                        context.chat_data[f'end_photo_sent_{user_id}'] = True
                        await update.message.reply_text(f"{session['trainer_name']}, фото окончания тренировки отправлено!")
                        return
                    else:
                        await update.message.reply_text("Нужна только одна фотография. Все остальные записи с тренировки отправляйте менеджеру в чат.")
                except Exception as e:
                    logging.error(f"Ошибка отправки фото: {e}")
                    await update.message.reply_text("Ошибка при публикации. Попробуйте позже.")
                    return
        
    await update.message.reply_text("Сейчас не время для фотоотчета или у вас нет тренировки в это время.")

# Обработка нажатия на кнопку "Отправить конечное фото"
# Этот обработчик проверяет время для отправки конечного фото
async def handle_end_photo_request(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    now = datetime.datetime.now(TASHKENT_TZ).time()
    
    trainer_sessions = get_trainer_info(user_id)
    if not trainer_sessions:
        await query.answer()
        await query.message.reply_text("Вы не зарегистрированы как тренер!")
        return
    
    for session in trainer_sessions:
        end_dt = datetime.datetime.strptime(session["end_time"], "%H:%M").time()
        end_early = (datetime.datetime.combine(datetime.date.today(), end_dt) - datetime.timedelta(minutes=12)).time()
        end_late = (datetime.datetime.combine(datetime.date.today(), end_dt) + datetime.timedelta(minutes=12)).time()
        
        if now < end_early:
            await query.answer()
            await query.message.reply_text("Вы отправляете фото не в то время. Тренировка еще не закончена.")
            return
        elif now > end_late:
            await query.answer()
            await query.message.reply_text("Тренировка закончилась слишком давно. Вы опоздали с фотоотчетом, вам начислен штраф.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Подробнее о штрафах", callback_data="fine_info")]]))
            return

# Обработка информации о штрафах
# Этот обработчик отображает информацию о штрафах тренерам
async def handle_fine_info(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "Если фотография отправляется не вовремя, тренеру назначается штраф 30% от суммы гонорара за эту тренировку. "
        "Фотоотчеты нужно отправлять в начале за 5 минут до начала тренировки или в течение 12 минут после ее начала. "
        "А также за 12 минут до окончания тренировки и в течение 12 минут после окончания."
    )

# Запуск бота
# Запускает бота и добавляет необходимые обработчики
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Отправить фото$"), handle_photo_request))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Запуск задачи обновления данных из Google Sheets каждые 5 минут
    job_queue = app.job_queue
    job_queue.run_repeating(update_google_sheet_data, interval=300, first=0)
    
    # Добавляем задачу напоминаний каждую минуту
    job_queue.run_repeating(send_training_reminders, interval=60, first=0)
    
    logger.info("Бот запущен...")
    app.run_polling()

# Отправка напоминаний о тренировках
# Функция отправляет напоминания тренерам о предстоящих тренировках
async def send_training_reminders(context: CallbackContext):
    """Функция напоминания о начале тренировки"""
    now = datetime.datetime.now(TASHKENT_TZ).time()
    for user_id in ADMIN_IDS:
        trainer_sessions = get_trainer_info(user_id)
        for session in trainer_sessions:
            start_time = datetime.datetime.strptime(session["start_time"], "%H:%M").time()
            if now == (datetime.datetime.combine(datetime.date.today(), start_time) - datetime.timedelta(minutes=60)).time():
                await context.bot.send_message(user_id, "Напоминание: тренировка через 1 час.")
            if now == (datetime.datetime.combine(datetime.date.today(), start_time) - datetime.timedelta(minutes=30)).time():
                await context.bot.send_message(user_id, "Напоминание: тренировка через 30 минут.")
            if now == (datetime.datetime.combine(datetime.date.today(), start_time) - datetime.timedelta(minutes=5)).time():
                await context.bot.send_message(user_id, "Напоминание: тренировка через 5 минут.")
            if now == (datetime.datetime.combine(datetime.date.today(), start_time) - datetime.timedelta(minutes=10)).time():
                await context.bot.send_message(user_id, "Напоминание: тренировка скоро!")

if __name__ == "__main__":
    main()
