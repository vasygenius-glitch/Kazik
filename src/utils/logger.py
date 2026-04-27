import os
from datetime import datetime

LOGS_DIR = "logs"

if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

def log_message(chat_id: int, chat_title: str, user_id: int, full_name: str, text: str):
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")

    # Файл для конкретной группы (один файл на день)
    filename = f"{LOGS_DIR}/chat_{chat_id}_{date_str}.txt"

    header = ""
    if not os.path.exists(filename):
        header = f"=== ИСТОРИЯ ЧАТА {chat_title} ({chat_id}) за {date_str} ===\n\n"

    with open(filename, "a", encoding="utf-8") as f:
        if header:
            f.write(header)

        clean_text = text.replace('\n', ' ')
        log_entry = f"[{time_str}] {full_name} ({user_id}): {clean_text}\n"
        f.write(log_entry)

def get_log_file(chat_id: int, date_str: str = None):
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        # Validate date_str format to prevent path traversal and ensure it's a valid date
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None

    # Use os.path.basename as an extra layer of security, though strptime already validates the format
    safe_date_str = os.path.basename(date_str)
    if safe_date_str != date_str:
        return None

    filename = os.path.join(LOGS_DIR, f"chat_{chat_id}_{safe_date_str}.txt")

    # Final check to ensure the path is within LOGS_DIR
    full_path = os.path.abspath(filename)
    logs_dir_path = os.path.abspath(LOGS_DIR)

    if not full_path.startswith(logs_dir_path):
        return None

    if os.path.exists(filename):
        return filename
    return None
