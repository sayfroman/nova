from telegram import Bot, Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, filters, CallbackContext, Updater, ConversationHandler
import random

# Константы для состояний
CHOOSE_BRANCH, CHOOSE_ACTION, SEND_PHOTO = range(3)

# Словари с текстами для публикаций
TXT_START = [
    "Тренировка началась!", "Поехали!", "Время тренировки!", "Готовы к тренировке!", "Начинаем!"
]
TXT_END = [
    "Тренировка завершена!", "Хорошая работа!", "Конец тренировки!", "Отличная тренировка!", "Все молодцы!"
]

# Привязка пользователей к филиалам
USER_CHANNELS = {
    6969603804: {
        "trainer_name": "Бунед",
        "branches": [
            {"id": "-1002331628469", "name": "295"},
            {"id": "-1002344879265", "name": "117"},
            {"id": "-1002214695720", "name": "44"}
        ]
    },
    413625395: {
        "trainer_name": "Алексей",
        "branches": [
            {"id": "-1002432571124", "name": "101"},
            {"id": "-1002460005367", "name": "254"}
        ]
    },
    735570267: {
        "trainer_name": "Марко",
        "branches": [
            {"id": "-1002323472696", "name": "307"},
            {"id": "-1002246173492", "name": "178"}
        ]
    },
    1532520919: {
        "trainer_name": "Сардор",
        "branches": [
            {"id": "-1002231891578", "name": "328"}
        ]
    },
    606134505: {
        "trainer_name": "Миржалол",
        "branches": [
            {"id": "-1002413556142", "name": "186"}
        ]
    },
    7666290317: {
        "trainer_name": "Адиба",
        "branches": [
            {"id": "-1002309219325", "name": "001"}
        ]
    }
}

# Функция старта
def start(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    if user_id in USER_CHANNELS:
        buttons = [[branch["name"]] for branch in USER_CHANNELS[user_id]["branches"]]
        reply_markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
        update.message.reply_text("Выберите филиал:", reply_markup=reply_markup)
        return CHOOSE_BRANCH
    else:
        update.message.reply_text("У вас нет доступа к филиалам.")
        return ConversationHandler.END

# Выбор филиала
def choose_branch(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    branch_name = update.message.text
    user_data = USER_CHANNELS.get(user_id, {})
    trainer_name = user_data.get("trainer_name", "Тренер")
    branches = user_data.get("branches", [])
    
    for branch in branches:
        if branch["name"] == branch_name:
            context.user_data["branch"] = branch
            context.user_data["trainer_name"] = trainer_name
            buttons = [["Отправить начало тренировки"], ["Отправить конец тренировки"], ["Выбрать филиал"]]
            reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
            update.message.reply_text(f"{trainer_name}, вы выбрали {branch_name}. Выберите действие:", reply_markup=reply_markup)
            return CHOOSE_ACTION
    
    update.message.reply_text("Неверный выбор. Попробуйте снова.")
    return CHOOSE_BRANCH

# Отправка фото
def send_photo(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if "branch" not in context.user_data:
        update.message.reply_text("Сначала выберите филиал.")
        return CHOOSE_BRANCH
    
    if not update.message.photo:
        update.message.reply_text("Пожалуйста, отправьте фото.")
        return SEND_PHOTO
    
    photo = update.message.photo[-1].file_id
    action = context.user_data.get("action")
    text = random.choice(TXT_START if action == "start" else TXT_END)
    channel_id = context.user_data["branch"]["id"]
    trainer_name = context.user_data["trainer_name"]
    context.bot.send_photo(chat_id=channel_id, photo=photo, caption=f"{trainer_name}: {text}")
    update.message.reply_text(f"Фото опубликовано в {context.user_data['branch']['name']}.")
    
    if action == "start":
        buttons = [["Отправить конец тренировки"], ["Выбрать филиал"]]
        reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
        update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    return CHOOSE_ACTION

# Выбор действия
def choose_action(update: Update, context: CallbackContext):
    text = update.message.text
    if text == "Отправить начало тренировки":
        context.user_data["action"] = "start"
        update.message.reply_text("Отправьте фото начала тренировки:", reply_markup=ReplyKeyboardRemove())
        return SEND_PHOTO
    elif text == "Отправить конец тренировки":
        context.user_data["action"] = "end"
        update.message.reply_text("Отправьте фото конца тренировки:", reply_markup=ReplyKeyboardRemove())
        return SEND_PHOTO
    elif text == "Выбрать филиал":
        return start(update, context)
    else:
        update.message.reply_text("Неверный выбор. Попробуйте снова.")
        return CHOOSE_ACTION

# Настройка обработчиков
updater = Updater("YOUR_BOT_TOKEN", use_context=True)
dp = updater.dispatcher
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CHOOSE_BRANCH: [MessageHandler(Filters.text & ~Filters.command, choose_branch)],
        CHOOSE_ACTION: [MessageHandler(Filters.text & ~Filters.command, choose_action)],
        SEND_PHOTO: [MessageHandler(Filters.photo, send_photo)]
    },
    fallbacks=[]
)
dp.add_handler(conv_handler)

# Запуск бота
updater.start_polling()
updater.idle()
