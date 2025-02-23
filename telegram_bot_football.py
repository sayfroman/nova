import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, JobQueue
import pytz

# Создаем объект для часового пояса Ташкента
TASHKENT_TZ = pytz.timezone('Asia/Tashkent')

# Расписание тренеров
schedule = [
    {"trainer_id": "6969603804", "name": "Бунед", "start": "17:00", "end": "18:00", "channel_id": "-1002331628469", "days": "Monday, Wednesday, Friday", "school": "Школа №295"},
    {"trainer_id": "413625395", "name": "Алексей", "start": "17:00", "end": "18:00", "channel_id": "-1002432571124", "days": "Monday, Wednesday, Friday", "school": "Школа №101"},
    {"trainer_id": "735570267", "name": "Марко", "start": "14:00", "end": "15:00", "channel_id": "-1002323472696", "days": "Monday, Wednesday, Friday", "school": "Школа №307"},
    {"trainer_id": "735570267", "name": "Марко", "start": "17:00", "end": "18:00", "channel_id": "-1002323472696", "days": "Monday, Wednesday, Friday", "school": "Школа №307"},
    {"trainer_id": "1532520919", "name": "Сардор", "start": "15:00", "end": "16:00", "channel_id": "-1002231891578", "days": "Monday, Wednesday, Friday", "school": "Школа №328"},
    {"trainer_id": "606134505", "name": "Миржалол", "start": "17:30", "end": "18:30", "channel_id": "-1002413556142", "days": "Tuesday, Thursday, Saturday", "school": "Школа №186"},
    {"trainer_id": "735570267", "name": "Марко", "start": "17:00", "end": "18:00", "channel_id": "-1002246173492", "days": "Tuesday, Thursday, Saturday", "school": "Школа №178"},
    {"trainer_id": "413625395", "name": "Алексей", "start": "15:00", "end": "16:00", "channel_id": "-1002460005367", "days": "Monday, Wednesday, Friday", "school": "Школа №254"},
    {"trainer_id": "6969603804", "name": "Бунед", "start": "15:00", "end": "16:00", "channel_id": "-1002344879265", "days": "Monday, Wednesday, Friday", "school": "Школа №117"},
    {"trainer_id": "7666290317", "name": "Адиба", "start": "14:00", "end": "15:00", "channel_id": "-1002309219325", "days": "Monday, Wednesday, Sunday", "school": "Школа №233"},
    {"trainer_id": "6969603804", "name": "Бунед", "start": "17:30", "end": "18:30", "channel_id": "-1002214695720", "days": "Tuesday, Thursday, Saturday", "school": "Школа №44"}
]

# Списки с вариантами текста для начала и конца тренировки
TXT_START_OPTIONS = [
    "Тренировка началась! Давайте разогреваться!",
    "Время тренировки наступило! Готовы к действию?",
    "Начинаем тренировку! Покажем класс!"
]

TXT_END_OPTIONS = [
    "Тренировка завершена! Спасибо всем за участие!",
    "Поздравляем с завершением тренировки! Молодцы!",
    "Тренировка окончена. Отлично поработали!"
]

# Функция для получения текущего времени
def get_current_time():
    return datetime.now(TASHKENT_TZ)

# Функция для выбора случайного текста из списка
def get_random_text(text_list):
    return random.choice(text_list)

# Функция для запуска бота
def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("Отправить начало тренировки", callback_data='start')],
        [InlineKeyboardButton("Отправить конец тренировки", callback_data='end')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Добро пожаловать в NOVA Assistant. Я буду помогать вам публиковать фотоотчеты.', reply_markup=reply_markup)

# Функция обработки нажатия на кнопки
def button(update: Update, context):
    query = update.callback_query
    trainer_id = str(query.from_user.id)
    
    # Определяем тексты в зависимости от выбранной кнопки
    if query.data == 'start':
        text = get_random_text(TXT_START_OPTIONS)
    elif query.data == 'end':
        text = get_random_text(TXT_END_OPTIONS)
    else:
        return
    
    # Определяем, какой тренер и канал
    current_time = get_current_time()
    day_of_week = current_time.strftime('%A')
    for entry in schedule:
        if entry['trainer_id'] == trainer_id and day_of_week in entry['days']:
            channel_id = entry['channel_id']
            context.bot.send_message(chat_id=channel_id, text=text)
            query.answer()
            break

# Функция отправки уведомлений за 10 минут до начала тренировки
def notify_before_training(context, job):
    trainer_id = job.context['trainer_id']
    current_time = get_current_time()
    day_of_week = current_time.strftime('%A')
    
    for entry in schedule:
        if entry['trainer_id'] == trainer_id and day_of_week in entry['days']:
            start_time = datetime.strptime(entry['start'], "%H:%M")
            start_time = TASHKENT_TZ.localize(start_time)  # Приводим время к часовому поясу Ташкента
            notify_time = start_time - timedelta(minutes=10)
            
            if current_time >= notify_time:
                context.bot.send_message(chat_id=trainer_id, text="Тренировка скоро начинается. Не забудьте опубликовать фотоотчет.")
            break

# Функция для проверки расписания и уведомлений
def schedule_notifications(update: Update, context):
    current_time = get_current_time()
    day_of_week = current_time.strftime('%A')
    
    for entry in schedule:
        if day_of_week in entry['days']:
            start_time = datetime.strptime(entry['start'], "%H:%M")
            start_time = TASHKENT_TZ.localize(start_time)
            notify_time = start_time - timedelta(minutes=10)
            
            context.job_queue.run_once(notify_before_training, notify_time, context={'trainer_id': entry['trainer_id']})

def main():
    # Настройка бота
    updater = Updater("YOUR_BOT_API_KEY", use_context=True)
    dp = updater.dispatcher
    job_queue = updater.job_queue
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))
    
    # Расписание уведомлений
    dp.add_handler(MessageHandler(Filters.text, schedule_notifications))
    
    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
