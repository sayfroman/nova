def add_trainer(trainer_id, name, start, end, channel_id, days, school):
    schedule_data = load_schedule()  # Загружаем текущее расписание
    new_trainer = {
        "trainer_id": trainer_id,
        "name": name,
        "start": start,
        "end": end,
        "channel_id": channel_id,
        "days": days,
        "school": school
    }
    schedule_data.append(new_trainer)  # Добавляем нового тренера
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(schedule_data, f, ensure_ascii=False, indent=4)  # Сохраняем изменения

def remove_trainer(trainer_id):
    schedule_data = load_schedule()  # Загружаем текущее расписание
    schedule_data = [trainer for trainer in schedule_data if trainer["trainer_id"] != trainer_id]  # Удаляем тренера
    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
        json.dump(schedule_data, f, ensure_ascii=False, indent=4)  # Сохраняем изменения
