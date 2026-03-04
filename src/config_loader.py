import json
import os
import shutil
import sys
from pathlib import Path

class ConfigLoader:
    @staticmethod
    def get_base_dir():
        """
        Определяет путь к ресурсам. 
        В .exe это временная папка PyInstaller (_MEIPASS), 
        в режиме разработки — корень проекта.
        """
        if getattr(sys, 'frozen', False):
            return Path(sys._MEIPASS)
        # Поднимаемся на уровень выше от src/
        return Path(__file__).parent.parent

    @staticmethod
    def get_config_dir():
        """Путь в APPDATA для сохранения настроек пользователя"""
        app_data = os.getenv('APPDATA')
        config_dir = Path(app_data) / "DigitalWallpaper"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    @staticmethod
    def load():
        """Загружает конфиг из APPDATA, если его нет — копирует дефолтный из ресурсов"""
        config_dir = ConfigLoader.get_config_dir()
        local_config = config_dir / "config.json"
        
        if not local_config.exists():
            # Ищем дефолтный конфиг там, где лежат ресурсы приложения
            base_dir = ConfigLoader.get_base_dir()
            bundle_config = base_dir / "config.json"
            
            if bundle_config.exists():
                shutil.copy(bundle_config, local_config)
            else:
                # Если файла нет совсем, создаем минимальный дефолт
                default_data = {
                    "window": {"bg_color": "#000000"},
                    "clock": {"font_name": "Arial", "font_size": 150, "font_color": "#DCDCDC", "show_seconds": True}
                }
                with open(local_config, 'w', encoding='utf-8') as f:
                    json.dump(default_data, f, indent=4)
                
        with open(local_config, 'r', encoding='utf-8') as f:
            return json.load(f)