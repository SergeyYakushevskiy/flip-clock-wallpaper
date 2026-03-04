import ctypes
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QGuiApplication, QIcon
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QSystemTrayIcon,
    QMenu,
    QApplication,
    QStyle,
)

from src.config_loader import ConfigLoader
from src.flip_digit import FlipDigit

GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_LAYERED = 0x00080000

SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

HWND_BOTTOM = 1


class LiveWallpaper(QWidget):
    def __init__(self, config):
        super().__init__()

        self.config = config
        self.timer = None

        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.main_layout)

        self.init_ui()
        self.init_tray()
        self.setup_desktop_mode()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)

        clock_cfg = self.config.get("clock", {})
        f_name = clock_cfg.get("font_name", "Arial")
        f_size = clock_cfg.get("font_size", 150)
        f_color = clock_cfg.get("font_color", "#DCDCDC")
        f_style = clock_cfg.get("font_style", "")

        self.digits = [FlipDigit(f_name, f_size, f_color, f_style) for _ in range(6)]

        self.main_layout.addWidget(self.digits[0])
        self.main_layout.addWidget(self.digits[1])
        self.add_separator()

        self.main_layout.addWidget(self.digits[2])
        self.main_layout.addWidget(self.digits[3])

        if clock_cfg.get("show_seconds", True):
            self.add_separator()
            self.main_layout.addWidget(self.digits[4])
            self.main_layout.addWidget(self.digits[5])

        self.apply_styles()
        self.update_geometry()

        if not self.timer:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_time)
            self.timer.start(1000)

        self.update_time()
        self.show()

    def add_separator(self):
        sep = QLabel(":")
        f_color = self.config["clock"].get("font_color", "#DCDCDC")
        sep.setStyleSheet(
            f"color: {f_color}; font-size: 90px; font-weight: bold; "
            f"border: none; background: transparent; margin-bottom: 10px;"
        )
        self.main_layout.addWidget(sep)

    def apply_styles(self):
        palette = self.palette()
        bg_color = self.config.get("window", {}).get("bg_color", "#000000")
        palette.setColor(self.backgroundRole(), QColor(bg_color))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def update_time(self):
        now = datetime.now()
        show_secs = self.config["clock"].get("show_seconds", True)
        time_str = now.strftime("%H%M%S" if show_secs else "%H%M")

        for i, digit_char in enumerate(time_str):
            if i < len(self.digits):
                self.digits[i].set_value(digit_char)

    def update_geometry(self):
        screens = QGuiApplication.screens()
        rect = screens[0].geometry()
        for s in screens:
            rect = rect.united(s.geometry())
        self.setGeometry(rect)

    def setup_desktop_mode(self):
        hwnd = int(self.winId())
        user32 = ctypes.windll.user32

        progman = user32.FindWindowW(b"Progman", None)
        result = ctypes.c_ulong()
        user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0, 1000, ctypes.byref(result))

        WorkerW = ctypes.c_int(0)

        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)

        def enum_windows(hwnd_enum, lParam):
            nonlocal WorkerW
            shell_def_view = user32.FindWindowExW(hwnd_enum, 0, b"SHELLDLL_DefView", None)
            if shell_def_view:
                WorkerW = user32.FindWindowExW(0, hwnd_enum, b"WorkerW", None)
            return True

        user32.EnumWindows(EnumWindowsProc(enum_windows), 0)
        if WorkerW != 0:
            user32.SetParent(hwnd, WorkerW)

        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        ex_style |= WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_LAYERED
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

        user32.SetWindowPos(
            hwnd,
            HWND_BOTTOM,
            0,
            0,
            0,
            0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW,
        )

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        base_path = Path(__file__).parent.parent
        icon_path = base_path / "assets" / "app_icon.ico"

        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))

        menu = QMenu()
        menu.addAction("Открыть конфиг").triggered.connect(self.open_config_file)
        menu.addAction("Обновить экран").triggered.connect(self.reload_config)
        menu.addSeparator()
        menu.addAction("Выход").triggered.connect(self.quit_app)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def open_config_file(self):
        config_path = ConfigLoader.get_config_dir() / "config.json"
        if config_path.exists():
            import os
            os.startfile(config_path)

    def reload_config(self):
        self.config = ConfigLoader.load()
        self.clear_layout(self.main_layout)

        clock_cfg = self.config.get("clock", {})
        f_name = clock_cfg.get("font_name", "Arial")
        f_size = clock_cfg.get("font_size", 150)
        f_color = clock_cfg.get("font_color", "#DCDCDC")
        f_style = clock_cfg.get("font_style", "")

        self.digits = [FlipDigit(f_name, f_size, f_color, f_style) for _ in range(6)]
        self.init_ui()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def quit_app(self):
        if self.timer:
            self.timer.stop()
        self.hide()
        self.tray_icon.hide()
        QApplication.instance().quit()
