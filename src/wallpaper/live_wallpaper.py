import logging
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, pyqtProperty, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QGuiApplication, QIcon, QColor
from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QSystemTrayIcon,
    QMenu,
    QApplication,
    QStyle,
)

from src.config.config_loader import ConfigLoader
from src.config.paths import ICONS_DIR
from src.ui.flip_digit import FlipDigit
from src.ui.settings_window import SettingsWindow
from src.config.logger import logger


# Win32 constants
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
WS_EX_LAYERED = 0x00080000

SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
HWND_BOTTOM = 1
WM_SPAWN_WORKER = 0x052C
LWA_ALPHA = 0x00000002
SW_SHOW = 5

class LiveWallpaper(QWidget):
    def __init__(self):
        logger.debug('инициализация живых обоев')
        super().__init__()

        self.config = ConfigLoader.load()
        self.digits = []
        self.timer = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)

        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.main_layout)

        self.settings_window = None

        QTimer.singleShot(0, self.init_ui_content)

        QApplication.processEvents()

        self.setup_desktop_mode()
        self.show()

        QTimer.singleShot(0, self.init_tray)
        self.start_clock()
        logger.debug('инициализация живых обоев прошла успешно')

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def init_ui_content(self):
        """Создает UI часов из конфига"""
        logger.debug('сборка UI')
        self.clear_layout(self.main_layout)
        clock_cfg = self.config.get("clock", {})
        font_name = clock_cfg.get("font_name", "Arial")
        font_size = clock_cfg.get("font_size", 150)
        font_color = clock_cfg.get("font_color", "#DCDCDC")
        font_style = clock_cfg.get("font_style", "")

        num_digits = 6 if clock_cfg.get("show_seconds", True) else 4
        logger.debug(f'количество цифр {num_digits}')

        self.digits = [
            FlipDigit(font_name, font_size, font_color, font_style)
            for _ in range(num_digits)
        ]

        self.main_layout.addWidget(self.digits[0])
        self.main_layout.addWidget(self.digits[1])

        self.add_separator()

        self.main_layout.addWidget(self.digits[2])
        self.main_layout.addWidget(self.digits[3])

        if num_digits == 6:
            self.add_separator()
            self.main_layout.addWidget(self.digits[4])
            self.main_layout.addWidget(self.digits[5])

        logger.debug('виджеты созданы')

        self.apply_styles()
        self.update_geometry()
        self.update_time()
        logger.debug('сборка UI успешно выполнена')

    def add_separator(self):
        sep = QLabel(":")
        font_color = self.config.get("clock", {}).get("font_color", "#DCDCDC")
        sep.setStyleSheet(
            f"""
            color: {font_color};
            font-size: 90px;
            font-weight: bold;
            border: none;
            background: transparent;
            margin-bottom: 10px;
            """
        )
        self.main_layout.addWidget(sep)

    def apply_styles(self):
        logger.debug('применение стилей')
        palette = self.palette()
        bg_color = self.config.get("window", {}).get("bg_color", "#000000")
        palette.setColor(self.backgroundRole(), QColor(bg_color))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        logger.debug('стили применены')


    # ---------------------------------------------------------
    # Clock logic
    # ---------------------------------------------------------

    def start_clock(self):
        logger.debug('запуск таймера синхронизации')
        if not self.timer:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_time)
            self.timer.start(1000)
        logger.debug('таймер успешно запущен')

    def update_time(self):
        now = datetime.now()
        show_seconds = self.config.get("clock", {}).get("show_seconds", True)
        time_str = now.strftime("%H%M%S" if show_seconds else "%H%M")

        for i, digit_char in enumerate(time_str):
            if i < len(self.digits):
                self.digits[i].set_value(digit_char)

    # ---------------------------------------------------------
    # Geometry
    # ---------------------------------------------------------

    def update_geometry(self):
        logger.debug('запущено обновление геометрии')
        screens = QGuiApplication.screens()
        rect = screens[0].geometry()
        for s in screens:
            rect = rect.united(s.geometry())
        self.setGeometry(rect)
        logger.debug('геометрия обновлена')

    # ---------------------------------------------------------
    # Desktop embedding
    # ---------------------------------------------------------

    def setup_desktop_mode(self):
        logger.debug('внедрение обоев в рабочий стол')
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32

        hwnd = int(self.winId())

        progman = user32.FindWindowW("Progman", None)
        user32.SendMessageTimeoutW(
            progman, 0x052C, 0, 0, 0x0000, 500, ctypes.byref(ctypes.c_ulong())
        )

        target_workerw = [0]

        def enum_windows(hwnd_enum, lParam):
            shell_view = user32.FindWindowExW(hwnd_enum, 0, "SHELLDLL_DefView", None)
            if shell_view:
                found = user32.FindWindowExW(0, hwnd_enum, "WorkerW", None)
                if found:
                    target_workerw[0] = found
            return True

        EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(EnumProc(enum_windows), 0)

        worker_w = target_workerw[0]
        if not worker_w:
            worker_w = user32.FindWindowW("WorkerW", None)
        if not worker_w:
            return

        user32.SetParent(hwnd, worker_w)
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        new_style = ex_style | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_LAYERED
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
        user32.SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)
        rect = QGuiApplication.primaryScreen().geometry()
        w, h = rect.width(), rect.height()
        user32.SetWindowPos(
            hwnd,
            0,
            0,
            0,
            w,
            h,
            SWP_SHOWWINDOW | SWP_NOACTIVATE
        )
        user32.ShowWindow(hwnd, SW_SHOW)
        user32.UpdateWindow(hwnd)
        logger.debug('внедрение обоев в рабочий стол прошло успешно')

    # ---------------------------------------------------------
    # Tray
    # ---------------------------------------------------------

    def init_tray(self):
        logger.debug('запуск обоев в трее')
        self.tray_icon = QSystemTrayIcon(self)
        logger.debug('инициализация иконки')
        QTimer.singleShot(0, self.init_tray_icon)
        logger.debug('инициализация иконки прошла успешно')
        logger.debug('инициализация меню трея')
        menu = QMenu()
        menu.addAction("Обновить экран").triggered.connect(self.reload_config)
        menu.addAction("Настройки").triggered.connect(self.open_settings)
        menu.addSeparator()
        menu.addAction("Выход").triggered.connect(self.quit_app)
        self.tray_icon.setContextMenu(menu)
        logger.debug('инициализация меню трея прошла успешно')
        logger.debug('запуск отображение')
        self.tray_icon.show()
        logger.debug('запуск обоев в трее прошло успешно')

    def init_tray_icon(self):
        icon_path = ICONS_DIR / "tray_icon.ico"
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            self.tray_icon.setIcon(
                self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            )

    # ---------------------------------------------------------
    # Settings
    # ---------------------------------------------------------
    def open_settings(self):
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.config, self)
            self.settings_window.destroyed.connect(self.on_settings_closed)
        self.settings_window.show()
        self.settings_window.setFocus()

    def on_settings_closed(self):
        self.settings_window = None

    def reload_config(self):
        logger.debug('обновление настроек')
        self.config = ConfigLoader.load()
        self.init_ui_content()
        self.show()
        logger.debug('настройки успешно обновлены')

    # ---------------------------------------------------------
    # Utils
    # ---------------------------------------------------------

    def clear_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def quit_app(self):
        if self.timer:
            self.timer.stop()
        self.tray_icon.hide()
        QApplication.instance().quit()