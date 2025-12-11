import os
from dotenv import load_dotenv

load_dotenv()  # завантажує .env

# Монети для моніторингу
SYMBOLS = ["APTUSDT", "TONUSDT", "SOLUSDT"]

# Поріг спреда у %, при якому бот реагує
THRESHOLD = 1  # 1.0%

# Інтервал оновлення (у секундах)
FETCH_INTERVAL = 1

# Телеграм токен і чат айді з середовища
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))