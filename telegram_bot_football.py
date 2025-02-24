import logging
import random
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Текстовые шаблоны
TXT_START = [
    "Начало тренировки! 💪",
    "Поехали! 🚀",
    "Время работать! ⏰",
    "Тренировка стартовала! 🏋️‍♂️",
    "Погнали! 🏃‍♂️"
]

TXT_END = [
    "Тренировка завершена! 🎉",
    "Отлично потрудились! 👏",
    "Завершение тренировки! ✅",
    "Молодцы! 🌟",
    "До следующей тренировки! 👋"
]

# Данные пользователей и филиалов
users = {
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

# Состояния пользователей
user_data = {}

async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in users:
        user_name = users[user_id]["trainer_name"]
        branch_names = [branch["name"] for branch in users[user_id]["branches"]]
        await update.message.reply_text(f"Привет, {user_name}! Выбери филиал:", reply_markup=ReplyKeyboardMarkup([branch_names], one_time_keyboard=True))
        user_data[user_id] = {"step": "choose_branch"}
    else:
        await update.message.reply_text("Извините, вы не зарегистрированы.")

async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id not in user_data:
        await update.message.reply_text("Пожалуйста, начните с команды /start.")
        return

    if user_data[user_id]["step"] == "choose_branch":
        branch_names = [branch["name"] for branch in users[user_id]["branches"]]
        if text in branch_names:
            user_data[user_id]["branch"] = next(branch for branch in users[user_id]["branches"] if branch["name"] == text)
            user_data[user_id]["step"] = "choose_action"
            await update.message.reply_text("Выбери действие:", reply_markup=ReplyKeyboardMarkup([["Отправить начало тренировки", "Отправить конец тренировки", "Выбрать филиал"]], one_time_keyboard=True))
        else:
            await update.message.reply_text("Пожалуйста, выбери филиал из списка.")

    elif user_data[user_id]["step"] == "choose_action":
        if text == "Отправить начало тренировки":
            user_data[user_id]["step"] = "send_start_photo"
            await update.message.reply_text("Отправь фотографию для начала тренировки.")
        elif text == "Отправить конец тренировки":
            user_data[user_id]["step"] = "send_end_photo"
            await update.message.reply_text("Отправь фотографию для конца тренировки.")
        elif text == "Выбрать филиал":
            user_data[user_id]["step"] = "choose_branch"
            branch_names = [branch["name"] for branch in users[user_id]["branches"]]
            await update.message.reply_text("Выбери филиал:", reply_markup=ReplyKeyboardMarkup([branch_names], one_time_keyboard=True))
        else:
            await update.message.reply_text("Пожалуйста, выбери действие из списка.")

async def handle_photo(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    photo = update.message.photo[-1].file_id

    if user_data[user_id]["step"] == "send_start_photo":
        branch = user_data[user_id]["branch"]
        channel_id = branch["id"]
        caption = random.choice(TXT_START)  # Случайный выбор текста
        await context.bot.send_photo(chat_id=channel_id, photo=photo, caption=caption)
        await update.message.reply_text(f"Фотография успешно опубликована в канале {branch['name']}.")
        user_data[user_id]["step"] = "choose_action"
        await update.message.reply_text("Выбери действие:", reply_markup=ReplyKeyboardMarkup([["Отправить конец тренировки", "Выбрать филиал"]], one_time_keyboard=True))

    elif user_data[user_id]["step"] == "send_end_photo":
        branch = user_data[user_id]["branch"]
        channel_id = branch["id"]
        caption = random.choice(TXT_END)  # Случайный выбор текста
        await context.bot.send_photo(chat_id=channel_id, photo=photo, caption=caption)
        await update.message.reply_text(f"Фотография успешно опубликована в канале {branch['name']}.")
        user_data[user_id]["step"] = "choose_action"
        await update.message.reply_text("Выбери действие:", reply_markup=ReplyKeyboardMarkup([["Отправить начало тренировки", "Выбрать филиал"]], one_time_keyboard=True))

async def main() -> None:
    # Вставьте сюда ваш токен
    application = Application.builder().token("7801498081:AAFCSe2aO5A2ZdnSqIblaf-45aRQQuybpqQ").build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Запускаем бота
    await application.run_polling()

if __name__ == '__main__':
    try:
        # Используем существующий цикл событий, если он уже запущен
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except RuntimeError as e:
        # Если цикл событий не запущен, создаем новый
        if "event loop is already running" in str(e):
            asyncio.run(main())
        else:
            raise e
