import json
import os

# Путь к файлу расписания
SCHEDULE_FILE = "schedule.json"

# Пример данных расписания
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

# Функция для загрузки данных из файла
def load_schedule():
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return schedule  # Возвращаем данные по умолчанию, если файл не существует

# Функция для сохранения данных в файл
def save_schedule():
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=4)

# Функция для поиска тренера по ID
def find_trainer_by_id(trainer_id):
    schedule_data = load_schedule()
    for trainer in schedule_data:
        if trainer["trainer_id"] == trainer_id:
            return trainer
    return None

# Функция для добавления нового тренера
def add_trainer(trainer_id, name, start, end, channel_id, days, school):
    new_trainer = {
        "trainer_id": trainer_id,
        "name": name,
        "start": start,
        "end": end,
        "channel_id": channel_id,
        "days": days,
        "school": school
    }
    schedule.append(new_trainer)
    save_schedule()

# Функция для удаления тренера по ID
def remove_trainer(trainer_id):
    global schedule
    schedule = [trainer for trainer in schedule if trainer["trainer_id"] != trainer_id]
    save_schedule()

# Пример использования
if __name__ == "__main__":
    load_schedule()  # Загрузка расписания
    add_trainer("1234567890", "Иван", "09:00", "10:00", "-100234567890", "Monday", "Школа №500")
    remove_trainer("413625395")  # Удаление тренера с ID 413625395
    save_schedule()  # Сохранение изменений в файл
