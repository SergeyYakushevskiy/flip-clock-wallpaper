import sys
from pathlib import Path
from src.config.app_info import APP_NAME
import os

# папка проекта
BASE_DIR = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent.parent.parent

# папка шрифтов
FONTS_DIR = BASE_DIR / "assets" / "fonts"

# папка иконок
ICONS_DIR = BASE_DIR / "assets" /"icons"

# папка пользователя
APPDATA_DIR = Path(os.getenv("APPDATA")) / APP_NAME

# папка с конфигом
CONFIG_DIR = APPDATA_DIR / "config"

# папка логов
LOG_DIR = APPDATA_DIR / "logs"

# пользовательский конфиг
USER_CONFIG_FILE = CONFIG_DIR / "config.json"

# дефолтный конфиг (внутри программы)
DEFAULT_CONFIG_FILE = BASE_DIR / "config" / "default_config.json"
