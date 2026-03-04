import ctypes
import os
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QAction, QGuiApplication
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSystemTrayIcon, QMenu, QApplication

from src.config_loader import ConfigLoader
from src.flip_digit import FlipDigit


class LiveWallpaper(QWidget):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self._enum_windows_callback = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)(self._enum_windows)
        self.workerw = 0

        self.init_ui()
        self.init_tray()
        self.set_to_background()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnBottomHint)

        # Фон "старый пластик"
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(self.config['window']['bg_color']))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(15)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Создаем сегменты (Часы : Минуты : Секунды)
        self.digits = [FlipDigit() for _ in range(6)]

        self.main_layout.addWidget(self.digits[0])
        self.main_layout.addWidget(self.digits[1])
        self.add_separator()
        self.main_layout.addWidget(self.digits[2])
        self.main_layout.addWidget(self.digits[3])

        if self.config['clock'].get('show_seconds', True):
            self.add_separator()
            self.main_layout.addWidget(self.digits[4])
            self.main_layout.addWidget(self.digits[5])

        self.setLayout(self.main_layout)
        self.update_geometry()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()
        self.show()

    def add_separator(self):
        sep = QLabel(":")
        sep.setStyleSheet("color: #444; font-size: 60px; font-weight: bold;")
        self.main_layout.addWidget(sep)

    def update_time(self):
        now = datetime.now()
        time_str = now.strftime("%H%M%S")
        for i, digit in enumerate(time_str):
            if i < len(self.digits):
                self.digits[i].set_value(digit)

    def open_config_folder(self):
        os.startfile(ConfigLoader.get_config_dir())

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        # Иконка (используем стандартную или вашу)
        self.tray_icon.setIcon(self.style().standardIcon(QAction.MenuRole.ApplicationSpecificRole))

        menu = QMenu()
        menu.addAction("Настроить (папка)").triggered.connect(self.open_config_folder)
        menu.addAction("Обновить конфиг").triggered.connect(self.reload_config)
        menu.addSeparator()
        menu.addAction("Выход").triggered.connect(QApplication.instance().quit)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def reload_config(self):
        self.config = ConfigLoader.load()
        # Применяем цвет фона
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(self.config['window']['bg_color']))
        self.setPalette(palette)
        # Скрываем/показываем секунды требует перезапуска для простоты лейаута
        self.update_time()

    def update_geometry(self):
        screens = QGuiApplication.screens()
        rect = screens[0].geometry()
        for s in screens: rect = rect.united(s.geometry())
        self.setGeometry(rect)

    def _enum_windows(self, h, l):
        if ctypes.windll.user32.FindWindowExW(h, 0, "SHELLDLL_DefView", None):
            self.workerw = ctypes.windll.user32.FindWindowExW(0, h, "WorkerW", None)
        return True

    def set_to_background(self):
        h = self.winId().__int__()
        prog = ctypes.windll.user32.FindWindowW("Progman", None)
        ctypes.windll.user32.SendMessageTimeoutW(prog, 0x052C, 0, 0, 0, 1000, None)
        ctypes.windll.user32.EnumWindows(self._enum_windows_callback, 0)
        ctypes.windll.user32.SetParent(h, self.workerw if self.workerw else prog)

    def cleanup_wallpaper(self):
        ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, None, 0x1 | 0x2)