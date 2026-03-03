"""
Digital Clock Live Wallpaper
----------------------------

Живые обои для Windows с цифровыми часами.
Работают через внедрение окна в WorkerW (за иконками рабочего стола).

Author: SergeyYakushevskiy
"""

from __future__ import annotations

import ctypes
import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QGuiApplication, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QVBoxLayout,
    QSystemTrayIcon,
    QMenu,
)


# ==============================
# Logging configuration
# ==============================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)


# ==============================
# Config Loader
# ==============================

class ConfigLoader:
    """
    Отвечает за загрузку и хранение конфигурации в AppData.
    """

    APP_FOLDER_NAME = "DigitalWallpaper"
    CONFIG_FILE_NAME = "config.json"

    @classmethod
    def get_config_dir(cls) -> Path:
        """
        Возвращает путь к директории конфигурации:
        C:\\Users\\<User>\\AppData\\Roaming\\DigitalWallpaper
        """
        app_data = os.getenv("APPDATA")
        if not app_data:
            raise RuntimeError("APPDATA environment variable not found")

        config_dir = Path(app_data) / cls.APP_FOLDER_NAME
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    @classmethod
    def load(cls) -> Dict[str, Any]:
        """
        Загружает конфигурацию.
        Если конфиг отсутствует в AppData — копирует шаблон.
        """
        config_dir = cls.get_config_dir()
        local_config = config_dir / cls.CONFIG_FILE_NAME

        if not local_config.exists():
            cls._copy_default_config(local_config)

        try:
            with open(local_config, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.exception("Failed to load config")
            raise RuntimeError("Invalid configuration file") from e

    @staticmethod
    def _copy_default_config(destination: Path) -> None:
        """
        Копирует config.json из директории приложения в AppData.
        """
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent

        source = base_dir / "config.json"

        if not source.exists():
            raise FileNotFoundError("Default config.json not found")

        try:
            shutil.copy(source, destination)
            logger.info("Default config copied to AppData")
        except Exception:
            logger.exception("Failed to copy default config")
            raise


# ==============================
# Windows Wallpaper Integration
# ==============================

class WindowsWallpaperManager:
    """
    Управляет внедрением окна в слой рабочего стола Windows.
    """

    def __init__(self) -> None:
        self.workerw = 0
        self._enum_callback = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.c_int, ctypes.c_int
        )(self._enum_windows)

    def attach(self, hwnd: int) -> None:
        """
        Встраивает окно в WorkerW.
        """
        user32 = ctypes.windll.user32

        progman = user32.FindWindowW("Progman", None)

        # Сообщение для создания WorkerW
        user32.SendMessageTimeoutW(
            progman,
            0x052C,
            0,
            0,
            0,
            1000,
            None,
        )

        user32.EnumWindows(self._enum_callback, 0)

        if self.workerw:
            user32.SetParent(hwnd, self.workerw)
        else:
            user32.SetParent(hwnd, progman)

    def _enum_windows(self, hwnd: int, _: int) -> bool:
        user32 = ctypes.windll.user32

        shell_dll = user32.FindWindowExW(
            hwnd, 0, "SHELLDLL_DefView", None
        )

        if shell_dll:
            self.workerw = user32.FindWindowExW(
                0, hwnd, "WorkerW", None
            )

        return True

    @staticmethod
    def cleanup() -> None:
        """
        Восстанавливает обои Windows.
        """
        ctypes.windll.user32.SystemParametersInfoW(
            0x0014, 0, None, 0x01 | 0x02
        )


# ==============================
# Main Wallpaper Widget
# ==============================

class LiveWallpaper(QWidget):
    """
    Главное окно живых обоев.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        super().__init__()
        self.config = config
        self.wallpaper_manager = WindowsWallpaperManager()

        self._init_ui()
        self._init_tray()
        self.wallpaper_manager.attach(int(self.winId()))

    # --------------------------
    # UI Initialization
    # --------------------------

    def _init_ui(self) -> None:
        self.setWindowTitle("Digital Clock Wallpaper")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnBottomHint
        )

        layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self._apply_styles()
        self._update_geometry()
        self._start_timer()

        self.show()

    def _apply_styles(self) -> None:
        """
        Применяет стили из config.json.
        """
        palette = self.palette()
        palette.setColor(
            self.backgroundRole(),
            QColor(self.config["window"]["bg_color"]),
        )
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        font = QFont(
            self.config["clock"]["font_name"],
            self.config["clock"]["font_size"],
        )

        self.label.setFont(font)
        self.label.setStyleSheet(
            f"color: {self.config['clock']['font_color']};"
        )

    def _start_timer(self) -> None:
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)
        interval = 1000
        self.timer.start(interval)
        self._update_time()

    # --------------------------
    # Time Handling
    # --------------------------

    def _update_time(self) -> None:
        show_seconds = self.config["clock"].get("show_seconds", True)
        fmt = "%H:%M:%S" if show_seconds else "%H:%M"
        self.label.setText(datetime.now().strftime(fmt))

    # --------------------------
    # System Tray
    # --------------------------

    def _init_tray(self) -> None:
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self._resolve_icon())

        menu = QMenu()

        menu.addAction("Открыть папку настроек", self._open_config_folder)
        menu.addAction("Обновить конфиг", self._reload_config)
        menu.addSeparator()
        menu.addAction("Выход", QApplication.instance().quit)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def _resolve_icon(self) -> QIcon:
        if getattr(sys, "frozen", False):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(__file__).parent

        icon_path = base_dir / "app_icon.ico"
        return QIcon(str(icon_path)) if icon_path.exists() else QIcon()

    def _open_config_folder(self) -> None:
        os.startfile(ConfigLoader.get_config_dir())

    def _reload_config(self) -> None:
        try:
            self.config = ConfigLoader.load()
            self._apply_styles()
            self._update_time()
            logger.info("Configuration reloaded")
        except Exception:
            logger.exception("Failed to reload config")

    # --------------------------
    # Screen Handling
    # --------------------------

    def _update_geometry(self) -> None:
        """
        Растягивает окно на все мониторы.
        """
        screens = QGuiApplication.screens()
        rect = screens[0].geometry()

        for screen in screens:
            rect = rect.united(screen.geometry())

        self.setGeometry(rect)


# ==============================
# Entry Point
# ==============================

def main() -> int:
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config = ConfigLoader.load()
    wallpaper = LiveWallpaper(config)

    exit_code = app.exec()
    WindowsWallpaperManager.cleanup()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
