import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from datetime import datetime, timedelta
import pytz
from telegram import Bot

# Указываем часовой пояс Ташкента
tashkent_tz = pytz.timezone('Asia/Tashkent')

# Настройки логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Авторизация в Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Football_School").sheet1

def get_trainer_schedule():
    data = sheet.get_all_records()
    schedule = {}
    for row in data:
        trainer_id = row["Trainer_ID"]
        schedule[trainer_id] = {
            "name": row["Trainer_Name"],
            "branch": row["Branch"],
            "start_time": row["Start_Time"],
            "end_time": row["End_Time"],
            "channel_id": row["Channel_ID"],
            "days_of_week": row["Days_of_Week"].split(", ")
        }
    return schedule

def should_accept_photo(trainer_id):
    schedule = get_trainer_schedule()
    now = datetime.now(tashkent_tz)
    today = now.strftime("%A")
    
    if trainer_id not in schedule:
        return False, "Вы не зарегистрированы в системе."
    
    trainer_info = schedule[trainer_id]
    if today not in trainer_info["days_of_week"]:
        return False, "Сегодня у вас нет тренировки. Если возникла ошибка, свяжитесь с менеджером."
    
    start_time = datetime.strptime(trainer_info["start_time"], "%H:%M").time()
    end_time = datetime.strptime(trainer_info["end_time"], "%H:%M").time()
    
    start_datetime = datetime.combine(now.date(), start_time).astimezone(tashkent_tz)
    end_datetime = datetime.combine(now.date(), end_time).astimezone(tashkent_tz)
    
    if now < start_datetime - timedelta(minutes=12):
        return False, "Тренировка еще не началась. Отправьте фото ближе ко времени начала."
    
    if now > end_datetime + timedelta(minutes=15):
        return False, "Вы опоздали с фотоотчетом. Учтите, что за опоздание вам будет назначен штраф в размере 30% от гонорара за эту тренировку."
    
    return True, ""

def process_photo(trainer_id, photo):
    accepted, message = should_accept_photo(trainer_id)
    if not accepted:
        return message
    
    schedule = get_trainer_schedule()
    trainer_info = schedule[trainer_id]
    channel_id = trainer_info["channel_id"]
    
    if not channel_id:
        logger.warning(f"Нет указанного Channel_ID для филиала {trainer_info['branch']}")
        return f"Внимание! У филиала {trainer_info['branch']} не указан канал для публикации. Добавьте Channel_ID в таблицу."
    
    bot = Bot(token="YOUR_BOT_TOKEN")
    bot.send_photo(chat_id=channel_id, photo=photo, caption=f"Фотоотчет от {trainer_info['name']} ({trainer_info['branch']})")
    
    return "Фото успешно опубликовано."

# Функция для периодического обновления данных каждые 10 минут
import time
while True:
    get_trainer_schedule()
    time.sleep(600)
