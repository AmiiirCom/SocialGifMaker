# logging_config.py
import logging
from config import LOG_FILE
import os

def setup_logging():
    # ایجاد پوشه لاگ در صورت نبود
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'),  # حالت بازنویسی
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("GifMaker")