import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from src.config_loader import ConfigLoader
from src.live_wallpaper import LiveWallpaper

sys.path.append(str(Path(__file__).parent))
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    wallpaper = LiveWallpaper(ConfigLoader.load())
    code = app.exec()
    sys.exit(code)