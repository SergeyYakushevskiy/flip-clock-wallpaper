import json
import os
import shutil
import sys
from pathlib import Path


class ConfigLoader:
    @staticmethod
    def get_config_dir():
        app_data = os.getenv('APPDATA')
        config_dir = Path(app_data) / "DigitalWallpaper"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    @staticmethod
    def load():
        config_dir = ConfigLoader.get_config_dir()
        local_config = config_dir / "config.json"
        if not local_config.exists():
            base_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
            bundle_config = base_dir / "config.json"
            if bundle_config.exists():
                shutil.copy(bundle_config, local_config)
        with open(local_config, 'r', encoding='utf-8') as f:
            return json.load(f)