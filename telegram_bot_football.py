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
sheet = gc.open_by_key("19vkwWg7jt6T5zjy9XpgYPQz0BA7mtfpSAt6s1hGA53g").sheet1

def update_google_sheet_data(context: CallbackContext):
    global sheet
    try:
        sheet = gc.open_by_key("19vkwWg7jt6T5zjy9XpgYPQz0BA7mtfpSAt6s1hGA53g").sheet1
        logger.info("Данные из Google Sheets обновлены")
    except Exception as e:
        logger.error(f"Ошибка обновления Google Sheets: {e}")

# Получение токена бота
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [5385649, 7368748440]

# Примеры сообщений
START_MESSAGES = [
    """🏆 Тренировка началась! Команда уже на поле!
    🏆 Mashg’ulot boshlandi! Jamoa maydonda!""",
    """⚽ Дети начали разминку, занятие в разгаре!
    ⚽ Bolalar qizishishni boshladi, mashg’ulot qizg‘in davom etmoqda!""",
    """🚀 Поехали! Наши юные футболисты уже тренируются! 
    🚀 Ketdik! Yosh futbolchilarimiz allaqachon mashg‘ulotda!""",
    """🔥 Тренировка стартовала! Сегодня работаем на максимум!
    🔥 Mashg‘ulot start oldi! Bugun maksimal darajada ishlaymiz!""",
    """💪 Мяч в игре! Начинаем занятие!
    💪 To‘p o‘yinda! Mashg‘ulotni boshladik!""",
    """⚡ Команда готова, тренировка в самом разгаре!
    ⚡ Jamoa tayyor, mashg‘ulot qizg‘in ketmoqda!""",
    """🏟️ Поле занято нашими чемпионами – тренировка идет!
    🏟️ Maydon bizning chempionlar bilan to‘ldi – mashg‘ulot boshlandi!""",
    """⏳ Без опозданий – разминка началась!
    ⏳ Kechikmang – qizishish allaqachon boshlandi!""",
    """🥅 Все на месте, тренировка в полном разгаре!
    🥅 Hamma joyida, mashg‘ulot qizg‘in davom etmoqda!""",
    """🌟 Стартуем! Сегодня – еще один шаг к победе!
    🌟 Boshladik! Bugun yana bir g‘alabaga yaqinlashamiz!""",
    """📢 Внимание, родители! Тренировка началась, работаем по плану!
    📢 Diqqat, ota-onalar! Mashg‘ulot boshlandi, rejaga muvofiq ishlayapmiz!""",
    """👟 Дети на поле, первые удары по мячу уже звучат!
    👟 Bolalar maydonda, to‘pga dastlabki zarbalar berildi!""",
    """💥 Заряжаемся энергией – тренировка в действии!
    💥 Energiyani yig‘amiz – mashg‘ulot davom etmoqda!""",
    """🏋️‍♂️ Физическая подготовка началась, готовимся к игре!
    🏋️‍♂️ Jismoniy tayyorgarlik boshlandi, o‘yin uchun hozirlik ko‘ramiz!""",
    """🚦 Зелёный свет! Тренировка пошла!
    🚦 Yashil chiroq! Mashg‘ulot boshlandi!""",
    """🎯 Фокус на игре – тренировка запущена!
    🎯 E’tibor faqat o‘yinda – mashg‘ulot boshlandi!""",
    """📅 По расписанию: начало тренировки!
    📅 Rejaga muvofiq: mashg‘ulot boshlandi!""",
    """🎶 Свисток прозвучал – команда в работе!
    🎶 Hushtak chalindi – jamoa harakatda!""",
    """🕒 Время тренировок! Сегодня снова растем!
    🕒 Mashg‘ulot vaqti! Bugun yana rivojlanamiz!""",
    """⚙️ Отрабатываем технику – тренировка в полном разгаре!
    ⚙️ Texnikani mashq qilamiz – mashg‘ulot qizg‘in ketmoqda!"""
]

END_MESSAGES = [
    """✅ Тренировка окончена! Все отлично потрудились!
    ✅ Mashg‘ulot tugadi! Hammasi zo‘r ishladi!""",
    """🏁 Финиш! Дети завершили занятие!
    🏁 Finish! Bolalar mashg‘ulotni tugatdi!""",
    """⚽ Тренировка подошла к концу, можно забирать игроков!
    ⚽ Mashg‘ulot tugadi, futbolchilarni olib ketish mumkin!""",
    """🔥 Отличная работа! Сегодня ребята показали класс!
    🔥 Ajoyib ish! Bugun bolalar juda yaxshi harakat qilishdi!""",
    """💪 Все потрудились на славу! До следующей тренировки!
    💪 Hamma a’lo darajada ishladi! Keyingi mashg‘ulotda ko‘rishamiz!""",
    """🚀 Занятие завершено, ждем вас на следующем!
    🚀 Mashg‘ulot yakunlandi, keyingisini kutamiz!""",
    """🏆 Тренировка закончена, впереди восстановление и отдых!
    🏆 Mashg‘ulot tugadi, oldinda dam olish va tiklanish!""",
    """🎉 Молодцы! Сегодняшняя тренировка – еще один шаг к успеху!
    🎉 Ajoyib ish! Bugungi mashg‘ulot g‘alabaga yana bir qadam!""",
    """⚡ Все выложились на максимум, пора отдыхать!
    ⚡ Hamma bor kuchini berdi, endi dam olish vaqti!""",
    """⏳ Занятие завершено, можно забирать будущих чемпионов!
    ⏳ Mashg‘ulot yakunlandi, kelajakdagi chempionlarni olib ketish mumkin!""",
    """🏅 Финальный свисток – тренировка окончена!
    🏅 Yakuniy hushtak – mashg‘ulot tugadi!""",
    """📢 Внимание, родители! Тренировка завершена, всех можно забирать!
    📢 Diqqat, ota-onalar! Mashg‘ulot tugadi, bolalarni olib ketishingiz mumkin!""",
    """🎯 Цели на сегодня выполнены, молодцы!
    🎯 Bugungi maqsadlar bajarildi, zo‘r ish!""",
    """💥 Футбольный день завершен, встречаемся на следующем занятии!
    💥 Futbol kuni yakunlandi, keyingi mashg‘ulotda ko‘rishamiz!""",
    """🕒 Время закончилось – тренировка подошла к концу!
    🕒 Vaqt tugadi – mashg‘ulot yakunlandi!""",
    """🥇 Достойная игра! Теперь на заслуженный отдых!
    🥇 Munosib o‘yin! Endi esa yaxshi dam olish kerak!""",
    """🔔 Финальный звонок, тренировка завершена!
    🔔 Yakuniy hushtak chalindi, mashg‘ulot tugadi!""",
    """🏆 Все отработано, теперь можно отдыхать!
    🏆 Hammasi a’lo bajarildi, endi esa dam olish vaqti!"""
]

# Хранение штрафов
PENALTIES = {}

# Получение данных тренера
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
async def handle_photo_request(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Пожалуйста, отправьте фото для отчета.")

# Обработка фото
async def handle_photo(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    now = datetime.datetime.now(TASHKENT_TZ).time()
    current_day = datetime.datetime.now(TASHKENT_TZ).strftime("%A")
    
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
        
        # Фотография начала тренировки
        if start_dt <= now <= (datetime.datetime.combine(datetime.date.today(), start_dt) + datetime.timedelta(minutes=12)).time():
            if update.message.photo:
                try:
                    if 'start_photo_sent' not in context.chat_data:
                        await context.bot.send_photo(chat_id=session["channel_id"], photo=update.message.photo[-1].file_id, caption=random.choice(START_MESSAGES))
                        context.chat_data['start_photo_sent'] = True
                        await update.message.reply_text(f"{session['trainer_name']}, фото начала тренировки отправлено! Нажмите кнопку ниже для отправки фото окончания тренировки.", reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("Отправить конечное фото", callback_data="send_end_photo")
                        ]]))
                        return
                    else:
                        await update.message.reply_text("Нужна только одна фотография. Все остальные записи с тренировки отправляйте менеджеру в чат.")
                except Exception as e:
                    logging.error(f"Ошибка отправки фото: {e}")
                    await update.message.reply_text("Ошибка при публикации. Попробуйте позже.")
                    return

        # Фотография конца тренировки
        if (datetime.datetime.combine(datetime.date.today(), end_dt) - datetime.timedelta(minutes=12)).time() <= now <= end_dt:
            if update.message.photo:
                try:
                    if 'end_photo_sent' not in context.chat_data:
                        await context.bot.send_photo(chat_id=session["channel_id"], photo=update.message.photo[-1].file_id, caption=random.choice(END_MESSAGES))
                        context.chat_data['end_photo_sent'] = True
                        await update.message.reply_text(f"{session['trainer_name']}, фото окончания тренировки отправлено!")
                        return
                    else:
                        await update.message.reply_text("Нужна только одна фотография. Все остальные записи с тренировки отправляйте менеджеру в чат.")
                except Exception as e:
                    logging.error(f"Ошибка отправки фото: {e}")
                    await update.message.reply_text("Ошибка при публикации. Попробуйте позже.")
                    return

    await update.message.reply_text("Сейчас не время для фотоотчета или у вас нет тренировки в это время.")

# Запуск бота
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

async def send_training_reminders(context: CallbackContext):
    """Функция отправляет уведомления тренерам о предстоящей тренировке."""
    now = datetime.datetime.now(TASHKENT_TZ).time()
    current_day = datetime.datetime.now(TASHKENT_TZ).strftime("%A")
    
    data = sheet.get_all_records()
    for row in data:
        try:
            start_dt = datetime.datetime.strptime(row["Start_Time"], "%H:%M").time()
            trainer_id = row.get("Trainer_ID")
            trainer_name = row.get("Trainer_Name", "Тренер")
            days_of_week_list = [day.strip() for day in row.get("Days_of_Week", "").split(",")]

            if current_day not in days_of_week_list:
                continue

            time_diffs = {
                "1_hour": datetime.timedelta(hours=1),
                "30_minutes": datetime.timedelta(minutes=30),
                "2_minutes": datetime.timedelta(minutes=2),
            }

            reminders = {
                "1_hour": "🚀 Через час у вас начинается тренировка. Не забудьте отправить фото вовремя!",
                "30_minutes": "⚡ Через полчаса начало тренировки. Убедитесь, что вы готовы!",
                "2_minutes": "⚽ Тренировка начинается, не забудьте отправить фотографию!",
            }

            for key, delta in time_diffs.items():
                reminder_time = (datetime.datetime.combine(datetime.date.today(), start_dt) - delta).time()
                if now >= reminder_time and now < (datetime.datetime.combine(datetime.date.today(), reminder_time) + datetime.timedelta(minutes=1)).time():
                    await context.bot.send_message(chat_id=trainer_id, text=reminders[key])

        except Exception as e:
            logging.error(f"Ошибка при отправке напоминаний: {e}")

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
