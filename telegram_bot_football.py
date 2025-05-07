import logging
import random
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
)

# === TOKEN ===
TOKEN = "7801498081:AAFCSe2aO5A2ZdnSqIblaf-45aRQQuybpqQ"

# === TRAINERS ===
TRAINERS = {
    699435808: {
        "name": "Джамиль ака",
        "branches": ["101", "216", "254"],
    },
    1532520919: {
        "name": "Сардор ака",
        "branches": ["328", "160"],
    },
    6969603804: {
        "name": "Бунед ака",
        "branches": ["117", "44"],
    },
    606134505: {
        "name": "Мирджалол",
        "branches": ["186"],
    },
    413625395: {
        "name": "Алексей",
        "branches": ["42"],
    },
}

# === CHANNELS ===
BRANCH_CHANNELS = {
    "42": -1002413556142,
    "186": -1002413556142,
    "117": -1002344879265,
    "44": -1002214695720,
    "328": -1002231891578,
    "160": -1002609810020,
    "101": -1002432571124,
    "216": -1002592035856,
    "254": -1002460005367,
}

# === TEXTS ===
MESSAGES_START = [
    "Тренировка началась! Дети в боевом настрое ⚽",
    "Мы только начали, но уже заряжены энергией!",
    "Первый свисток! Погнали!",
    "Разминка пошла! Сила, ловкость, выносливость!",
    "Сегодня работаем на максимум — тренировка началась!",
    "Время побеждать — тренировка стартовала!",
    "Заряжаем детей энергией! Начало положено.",
    "Вперед к новым победам! Тренировка в самом разгаре.",
    "Прекрасная погода и боевой настрой — мы начали!",
    "Движение — это жизнь! Начали тренировку!",
]

MESSAGES_END = [
    "Тренировка завершена! Все молодцы!",
    "Дети выложились на максимум — спасибо за внимание 💪",
    "Сегодня было жарко! Тренировка подошла к концу.",
    "Устали, но довольны! До следующей встречи!",
    "Отлично поработали! Все старались.",
    "Футбольная магия завершена — до новых побед!",
    "Тренировка окончена. Дети молодцы!",
    "Было круто — спасибо всем за участие!",
    "Пора домой отдыхать! Завтра снова в бой!",
    "До новых встреч на поле! Отличная тренировка!",
]

# === СТАДИИ ===
SELECT_BRANCH, SELECT_ACTION, WAIT_PHOTO = range(3)

# === ЛОГИ ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === ХЭНДЛЕРЫ ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    trainer = TRAINERS.get(user_id)

    if not trainer:
        await update.message.reply_text("🚫 У вас нет доступа к этому боту.")
        return ConversationHandler.END

    context.user_data["name"] = trainer["name"]
    context.user_data["branches"] = trainer["branches"]

    await update.message.reply_text(
        f"Добро пожаловать, {trainer['name']}!\n"
        "Я помогу вам публиковать фотоотчеты в родительские каналы.\n"
        "Выберите филиал:",
        reply_markup=ReplyKeyboardMarkup(
            [[branch] for branch in trainer["branches"]],
            resize_keyboard=True,
            one_time_keyboard=True
        ),
    )
    return SELECT_BRANCH

async def select_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    selected_branch = update.message.text
    if selected_branch not in context.user_data["branches"]:
        await update.message.reply_text("❌ Филиал не найден. Попробуйте снова.")
        return SELECT_BRANCH

    context.user_data["branch"] = selected_branch
    await update.message.reply_text(
        f"📍 Филиал выбран: {selected_branch}\nЧто вы хотите сделать?",
        reply_markup=ReplyKeyboardMarkup(
            [["Начало тренировки", "Конец тренировки"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return SELECT_ACTION

async def select_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = update.message.text
    if action not in ["Начало тренировки", "Конец тренировки"]:
        await update.message.reply_text("❌ Неизвестное действие.")
        return SELECT_ACTION

    context.user_data["action"] = action
    await update.message.reply_text("📸 Пожалуйста, отправьте фотографию.")
    return WAIT_PHOTO

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1].file_id
    branch = context.user_data["branch"]
    action = context.user_data["action"]

    text = random.choice(MESSAGES_START if action == "Начало тренировки" else MESSAGES_END)
    caption = f"{text}\n📍 Филиал: {branch}"

    channel = BRANCH_CHANNELS.get(branch)
    if channel:
        await context.bot.send_photo(chat_id=channel, photo=photo, caption=caption)
        await update.message.reply_text("✅ Фото успешно опубликовано.")

        if action == "Начало тренировки":
            await update.message.reply_text("🕓 Ждем фотографию конца тренировки.")
        else:
            await update.message.reply_text("🎉 Отличная работа! Спасибо, что провели эту тренировку.")

        # Вернуться к выбору филиала
        await update.message.reply_text(
            "Выберите филиал:",
            reply_markup=ReplyKeyboardMarkup(
                [[branch] for branch in context.user_data["branches"]],
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return SELECT_BRANCH
    else:
        await update.message.reply_text("❌ Ошибка: Канал не найден.")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚪 Вы вышли из процесса.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# === MAIN ===

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_BRANCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_branch)],
            SELECT_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_action)],
            WAIT_PHOTO: [MessageHandler(filters.PHOTO, receive_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    logger.info("🚀 Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
