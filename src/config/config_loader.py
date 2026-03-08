import json
import shutil

from src.config.paths import (
    CONFIG_DIR,
    USER_CONFIG_FILE,
    DEFAULT_CONFIG_FILE
)

from src.config.logger import logger


class ConfigLoader:
    @staticmethod
    def ensure_directories():
        """Создаёт необходимые директории"""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def ensure_user_config():
        """
        Если пользовательского конфига нет —
        копирует дефолтный из ресурсов приложения.
        """
        if not USER_CONFIG_FILE.exists():
            if not DEFAULT_CONFIG_FILE.exists():
                raise FileNotFoundError(
                    f"файл не найден: {DEFAULT_CONFIG_FILE}"
                )

            shutil.copy(DEFAULT_CONFIG_FILE, USER_CONFIG_FILE)

    @staticmethod
    def load():
        """Загружает конфиг"""
        logger.debug('инициализация структуры папок')
        ConfigLoader.ensure_directories()
        ConfigLoader.ensure_user_config()
        logger.debug('загрузка файла настроек')
        with open(USER_CONFIG_FILE, "r", encoding="utf-8") as f:
            logger.debug('Файл настроек загружен')
            return json.load(f)
