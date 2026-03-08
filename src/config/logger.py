import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

from src.config.paths import LOG_DIR


def get_log_filename(base_log_dir=LOG_DIR):
    """
    Возвращает имя файла лога на основе текущей даты.
    Если файл уже существует, добавляет номер в скобках.
    """
    # Создаем директорию для логов, если её нет
    base_log_dir.mkdir(parents=True, exist_ok=True)

    # Только дата в формате ГГГГ-ММ-ДД
    base_name = datetime.now().strftime("%Y-%m-%d")

    # Полный путь к файлу
    file_path = base_log_dir / f"{base_name}.log"

    # Если файл не существует, возвращаем его
    if not file_path.exists():
        return file_path

    # Если существует, ищем свободный номер
    counter = 1
    while True:
        new_file_path = base_log_dir / f"{base_name}({counter}).log"
        if not new_file_path.exists():
            return new_file_path
        counter += 1

def setup_logger(log_file):
    logger = logging.getLogger("flipclock")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info('start processing')

    return logger

LOG_FILE = get_log_filename()
logger = setup_logger(LOG_FILE)
