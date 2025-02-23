import json
from datetime import datetime

PENALTIES_FILE = 'penalties.json'

def load_penalties():
    """Загружает данные о штрафах из файла."""
    try:
        with open(PENALTIES_FILE, 'r', encoding='utf-8') as file:
            penalties = json.load(file)
            return penalties
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def save_penalties(penalties):
    """Сохраняет данные о штрафах в файл."""
    with open(PENALTIES_FILE, 'w', encoding='utf-8') as file:
        json.dump(penalties, file, ensure_ascii=False, indent=4)

def log_penalty(trainer_id):
    """Записывает штраф для тренера."""
    penalties = load_penalties()
    penalty = {
        'trainer_id': trainer_id,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    penalties.append(penalty)
    save_penalties(penalties)
    print(f"Штраф для тренера {trainer_id} записан.")

def get_penalties():
    """Получает все штрафы."""
    return load_penalties()

def get_penalties_by_trainer(trainer_id):
    """Получает все штрафы для конкретного тренера."""
    penalties = load_penalties()
    return [penalty for penalty in penalties if penalty['trainer_id'] == trainer_id]
