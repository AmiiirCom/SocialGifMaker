"""
Logging configuration for the application.
Logs are written to a file and also printed to stdout.
"""

import logging
import os
from config import LOG_FILE


def setup_logging() -> logging.Logger:
    """Configure and return a logger instance."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("GifMaker")