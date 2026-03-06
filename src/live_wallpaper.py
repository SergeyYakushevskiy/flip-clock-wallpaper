from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
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

from src.flip_digit import FlipDigit

# Константы Win32 API
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
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.digits = []
        self.timer = None

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)

        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(20)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.main_layout)

        self.init_ui_content()

        self.show()
        QApplication.processEvents()

        self.setup_desktop_mode()

        self.init_tray()
        self.start_clock()

    def init_ui_content(self):
        """Создает или пересоздает виджеты часов на основе конфига"""
        self.clear_layout(self.main_layout)

        clock_cfg = self.config.get("clock", {})
        f_name = clock_cfg.get("font_name", "Arial")
        f_size = clock_cfg.get("font_size", 150)
        f_color = clock_cfg.get("font_color", "#DCDCDC")
        f_style = clock_cfg.get("font_style", "")


        num_digits = 6 if clock_cfg.get("show_seconds", True) else 4
        self.digits = [FlipDigit(f_name, f_size, f_color, f_style) for _ in range(num_digits)]

        # Сборка интерфейса
        self.main_layout.addWidget(self.digits[0])
        self.main_layout.addWidget(self.digits[1])
        self.add_separator()
        self.main_layout.addWidget(self.digits[2])
        self.main_layout.addWidget(self.digits[3])

        if num_digits == 6:
            self.add_separator()
            self.main_layout.addWidget(self.digits[4])
            self.main_layout.addWidget(self.digits[5])

        self.apply_styles()
        self.update_geometry()
        self.update_time()

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

    def start_clock(self):
        if not self.timer:
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_time)
            self.timer.start(1000)

    def update_geometry(self):
        screens = QGuiApplication.screens()
        rect = screens[0].geometry()
        for s in screens:
            rect = rect.united(s.geometry())
        self.setGeometry(rect)

    def setup_desktop_mode(self):
        """
        Прод-уровень: встраивание окна в структуру WorkerW.
        Исправлено: добавлен Layered Alpha и форсированная перерисовка.
        """
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.windll.user32

        hwnd = int(self.winId())

        # Подготовка слоев Windows
        progman = user32.FindWindowW("Progman", None)
        user32.SendMessageTimeoutW(
            progman, 0x052C, 0, 0, 0x0000, 1000, ctypes.byref(ctypes.c_ulong())
        )

        # Поиск целевого WorkerW (слой под иконками)
        target_workerw = [0]

        def enum_windows(hwnd_enum, lParam):
            shell_view = user32.FindWindowExW(hwnd_enum, 0, "SHELLDLL_DefView", None)
            if shell_view:
                # Находим WorkerW, который идет сразу за SHELLDLL_DefView
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


        # Установка родителя
        user32.SetParent(hwnd, worker_w)

        # Настройка расширенных стилей
        # WS_EX_TOOLWINDOW: убрать из панели задач
        # WS_EX_NOACTIVATE: не перехватывать фокус (клики сквозь иконки)
        # WS_EX_LAYERED: необходимо для корректного композитинга в WorkerW
        ex_style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        new_style = ex_style | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE | WS_EX_LAYERED
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

        user32.SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)

        # Финальное позиционирование и отображение
        # SWP_SHOWWINDOW, чтобы окно точно было активным внутри родителя
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            rect = QGuiApplication.primaryScreen().geometry()
            w, h = rect.width(), rect.height()

        user32.SetWindowPos(
            hwnd, 0,
            0, 0, w, h,
            SWP_SHOWWINDOW | SWP_NOACTIVATE
        )

        # Принудительно показываем окно через API
        user32.ShowWindow(hwnd, SW_SHOW)
        user32.UpdateWindow(hwnd)


    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        base_path = Path(__file__).parent.parent
        icon_path = base_path / "assets" / "icons" / "tray_icon.ico"
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
        from src.config_loader import ConfigLoader
        config_path = ConfigLoader.get_config_dir() / "config.json"
        if config_path.exists():
            import os
            os.startfile(config_path)

    def reload_config(self):
        """Метод мягкого обновления без перезапуска всего Win32 процесса"""
        from src.config_loader import ConfigLoader
        self.config = ConfigLoader.load()
        self.init_ui_content()
        self.show()

    def clear_layout(self, layout):
        if layout is not None:
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