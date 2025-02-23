# Correcting the syntax error by properly formatting the string with triple quotes
penalties_py_code = '''
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

def log_penalty(trainer_name, penalty_reason):
    """Записывает штраф для тренера."""
    penalties = load_penalties()
    penalty = {
        'trainer_name': trainer_name,
        'penalty_date': datetime.now().strftime('%Y-%m-%d'),
        'penalty_time': datetime.now().strftime('%H:%M:%S'),
        'penalty_reason': penalty_reason
    }
    penalties.append(penalty)
    save_penalties(penalties)
    print(f"Штраф для тренера {trainer_name} записан.")

def get_penalties():
    """Получает все штрафы."""
    return load_penalties()

def get_penalties_by_trainer(trainer_name):
    """Получает все штрафы для конкретного тренера."""
    penalties = load_penalties()
    return [penalty for penalty in penalties if penalty['trainer_name'] == trainer_name]
'''

# Save the corrected penalties.py code to a file
penalties_py_path = '/mnt/data/penalties.py'
with open(penalties_py_path, 'w', encoding='utf-8') as f:
    f.write(penalties_py_code)

penalties_py_path
