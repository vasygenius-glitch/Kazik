import os
from dotenv import load_dotenv

# Ищем .env файл в корне проекта, относительно текущего файла
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
env_path = os.path.join(root_dir, '.env')

load_dotenv(dotenv_path=env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH", "firebase-key.json")
CREATOR_USERNAME = os.getenv("CREATOR_USERNAME", "z_1l1")
try:
    CREATOR_ID = int(os.getenv("CREATOR_ID", "0"))
except ValueError:
    CREATOR_ID = 0
