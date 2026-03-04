import sys

from PyQt6.QtWidgets import QApplication

from src.config_loader import ConfigLoader
from src.live_wallpaper import LiveWallpaper

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    wallpaper = LiveWallpaper(ConfigLoader.load())
    code = app.exec()
    wallpaper.cleanup_wallpaper()
    sys.exit(code)