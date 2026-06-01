import os
import logging
import shutil
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(SCRIPT_DIR, "logs")
DEBUG_SCREENSHOTS_DIR = os.path.join(LOG_DIR, "debug_screenshots")


def get_logger(name):
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    os.makedirs(LOG_DIR, exist_ok=True)

    _clean_old_logs()

    log_filename = datetime.now().strftime("%Y-%m-%d") + ".log"
    log_path = os.path.join(LOG_DIR, log_filename)

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)-7s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] [%(levelname)-7s] %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(console_handler)

    return logger


def get_screenshot_path(name):
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%H%M%S")
    screenshot_dir = os.path.join(DEBUG_SCREENSHOTS_DIR, today)
    os.makedirs(screenshot_dir, exist_ok=True)
    return os.path.join(screenshot_dir, f"{name}_{timestamp}.png")


def _clean_old_logs(days=7):
    cutoff = datetime.now() - timedelta(days=days)

    if os.path.isdir(LOG_DIR):
        for entry in os.listdir(LOG_DIR):
            entry_path = os.path.join(LOG_DIR, entry)
            if os.path.isfile(entry_path) and entry.endswith(".log"):
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(entry_path))
                    if mtime < cutoff:
                        os.remove(entry_path)
                except Exception:
                    pass

    if os.path.isdir(DEBUG_SCREENSHOTS_DIR):
        for folder in os.listdir(DEBUG_SCREENSHOTS_DIR):
            folder_path = os.path.join(DEBUG_SCREENSHOTS_DIR, folder)
            if os.path.isdir(folder_path):
                try:
                    folder_date = datetime.strptime(folder, "%Y-%m-%d")
                    if folder_date < cutoff:
                        shutil.rmtree(folder_path, ignore_errors=True)
                except ValueError:
                    pass
