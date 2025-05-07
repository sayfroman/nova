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
    5385649: {
        "name": "Повелитель",
        "branches": ["42","186","101","216","254","328","160","117","44","001"],
    },
    80125926: {
        "name": "Босс",
        "branches": ["42","186","101","216","254","328","160","117","44","001"],
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
    "001": -1002309219325,
}

# === TEXTS ===
MESSAGES_START = [
    "🏆 Тренировка началась! Команда уже на поле!\n🏆 Mashg’ulot boshlandi! Jamoa maydonda!",
    "⚽ Дети начали разминку, занятие в разгаре!\n⚽ Bolalar qizishishni boshladi, mashg’ulot qizg’in davom etmoqda!",
    "🚀 Поехали! Наши юные футболисты уже тренируются!\n🚀 Ketdik! Yosh futbolchilarimiz allaqachon mashg’ulotda!",
    "🔥 Тренировка стартовала! Сегодня работаем на максимум!\n🔥 Mashg’ulot start oldi! Bugun maksimal darajada ishlaymiz!",
    "💪 Мяч в игре! Начинаем занятие!\n💪 To‘p o‘yinda! Mashg‘ulotni boshladik!",
    "⚡ Команда готова, тренировка в самом разгаре!\n⚡ Jamoa tayyor, mashg’ulot qizg’in ketmoqda!",
    "🏟️ Поле занято нашими чемпионами – тренировка идет!\n🏟️ Maydon bizning chempionlar bilan to‘ldi – mashg‘ulot boshlandi!",
    "⏳ Без опозданий – разминка началась!\n⏳ Kechikmang – qizishish allaqachon boshlandi!",
    "🥅 Все на месте, тренировка в полном разгаре!\n🥅 Hamma joyida, mashg‘ulot qizg‘in davom etmoqda!",
    "🌟 Стартуем! Сегодня – еще один шаг к победе!\n🌟 Boshladik! Bugun yana bir g‘alabaga yaqinlashamiz!",
    "📢 Внимание, родители! Тренировка началась, работаем по плану!\n📢 Diqqat, ota-onalar! Mashg‘ulot boshlandi, rejaga muvofiq ishlayapmiz!",
    "👟 Дети на поле, первые удары по мячу уже звучат!\n👟 Bolalar maydonda, to‘pga dastlabki zarbalar berildi!",
    "💥 Заряжаемся энергией – тренировка в действии!\n💥 Energiyani yig‘amiz – mashg‘ulot davom etmoqda!",
    "🏋️‍♂️ Физическая подготовка началась, готовимся к игре!\n🏋️‍♂️ Jismoniy tayyorgarlik boshlandi, o‘yin uchun hozirlik ko‘ramiz!",
    "🚦 Зелёный свет! Тренировка пошла!\n🚦 Yashil chiroq! Mashg‘ulot boshlandi!",
    "🎯 Фокус на игре – тренировка запущена!\n🎯 E’tibor faqat o‘yinda – mashg‘ulot boshlandi!",
    "📅 По расписанию: начало тренировки!\n📅 Rejaga muvofiq: mashg‘ulot boshlandi!",
    "🎶 Свисток прозвучал – команда в работе!\n🎶 Hushtak chalindi – jamoa harakatda!",
    "🕒 Время тренировок! Сегодня снова растем!\n🕒 Mashg‘ulot vaqti! Bugun yana rivojlanamiz!",
    "⚙️ Отрабатываем технику – тренировка в полном разгаре!\n⚙️ Texnikani mashq qilamiz – mashg‘ulot qizg‘in ketmoqda!",
]

MESSAGES_END = [
    "✅ Тренировка окончена! Все отлично потрудились!\n✅ Mashg’ulot tugadi! Hammasi zo‘r ishladi!",
    "🏁 Финиш! Дети завершили занятие!\n🏁 Finish! Bolalar mashg‘ulotni tugatdi",
    "⚽ Тренировка подошла к концу, можно забирать игроков!\n⚽ Mashg‘ulot tugadi, futbolchilarni olib ketish mumkin!",
    "🔥 Отличная работа! Сегодня ребята показали класс!\n🔥 Ajoyib ish! Bugun bolalar juda yaxshi harakat qilishdi!",
    "💪 Все потрудились на славу! До следующей тренировки!\n💪 Hamma a’lo darajada ishladi Keyingi mashg‘ulotda ko‘rishamiz!",
    "🚀 Занятие завершено, ждем вас на следующем!\n🚀 Mashg‘ulot yakunlandi, keyingisini kutamiz!",
    "🏆 Тренировка закончена, впереди восстановление и отдых!\n🏆 Mashg‘ulot tugadi, oldinda dam olish va tiklanish!",
    "🎉 Молодцы! Сегодняшняя тренировка – еще один шаг к успеху!\n🎉 Ajoyib ish! Bugungi mashg‘ulot g‘alabaga yana bir qadam!",
    "⚡ Все выложились на максимум, пора отдыхать!\n⚡ Hamma bor kuchini berdi, endi dam olish vaqti!",
    "⏳ Занятие завершено, можно забирать будущих чемпионов!\n⏳ Mashg‘ulot yakunlandi, kelajakdagi chempionlarni olib ketish mumkin!",
    "🏅 Финальный свисток – тренировка окончена!\n🏅 Yakuniy hushtak – mashg‘ulot tugadi!",
    "📢 Внимание, родители! Тренировка завершена, всех можно забирать!\n📢 Diqqat, ota-onalar! Mashg‘ulot tugadi, bolalarni olib ketishingiz mumkin!",
    "🎯 Цели на сегодня выполнены, молодцы!\n🎯 Bugungi maqsadlar bajarildi, zo‘r ish!",
    "💥 Футбольный день завершен, встречаемся на следующем занятии!\n💥 Futbol kuni yakunlandi, keyingi mashg‘ulotda ko‘rishamiz!",
    "🕒 Время закончилось – тренировка подошла к концу!\n🕒 Vaqt tugadi – mashg‘ulot yakunlandi!",
    "🥇 Достойная игра! Теперь на заслуженный отдых!\n🥇 Munosib o‘yin! Endi esa yaxshi dam olish kerak!",
    "🔔 Финальный звонок, тренировка завершена!\n🔔 Yakuniy hushtak chalindi, mashg‘ulot tugadi!",
    "🏆 Все отработано, теперь можно отдыхать!\n🏆 Hammasi a’lo bajarildi, endi esa dam olish vaqti!",
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
