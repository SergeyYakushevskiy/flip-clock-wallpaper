import os
import sys
import json
import ctypes
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QSystemTrayIcon, QMenu
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QGuiApplication, QAction, QIcon

class ConfigLoader:
    @staticmethod
    def get_config_dir():
        # Путь: C:\Users\Имя\AppData\Roaming\DigitalWallpaper
        app_data = os.getenv('APPDATA')
        config_dir = Path(app_data) / "DigitalWallpaper"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    @staticmethod
    def load():
        config_dir = ConfigLoader.get_config_dir()
        local_config = config_dir / "config.json"
        
        # Если в AppData нет конфига, копируем его из папки с EXE (шаблон)
        if not local_config.exists():
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent
            else:
                base_dir = Path(__file__).parent
                
            bundle_config = base_dir / "config.json"
            
            if bundle_config.exists():
                try:
                    shutil.copy(bundle_config, local_config)
                except Exception as e:
                    print(f"Ошибка копирования: {e}")

        # Читаем ТОЛЬКО из AppData
        with open(local_config, 'r', encoding='utf-8') as f:
            return json.load(f)

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
        self.setWindowTitle("Digital Clock Wallpaper")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnBottomHint)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        
        self.layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

        self.apply_styles()
        self.update_geometry()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()
        self.show()

    def apply_styles(self):
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(self.config['window']['bg_color']))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        font = QFont(self.config['clock']['font_name'], self.config['clock']['font_size'])
        self.label.setFont(font)
        self.label.setStyleSheet(f"color: {self.config['clock']['font_color']}; border: none;")

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, "app_icon.ico")
        else:
            icon_path = os.path.join(os.path.dirname(__file__), "app_icon.ico")
            
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(QAction.MenuRole.ApplicationSpecificRole))
        
        tray_menu = QMenu()
        
        # КИЛЛЕР-ФИЧА: Открыть папку с настройками
        open_config_action = tray_menu.addAction("Настроить (открыть папку)")
        open_config_action.triggered.connect(self.open_config_folder)
        
        reload_action = tray_menu.addAction("Обновить конфиг")
        reload_action.triggered.connect(self.reload_config)
        
        tray_menu.addSeparator()
        
        exit_action = tray_menu.addAction("Выход")
        exit_action.triggered.connect(QApplication.instance().quit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def open_config_folder(self):
        """Открывает папку в AppData через Проводник"""
        config_dir = ConfigLoader.get_config_dir()
        os.startfile(config_dir)

    def reload_config(self):
        try:
            self.config = ConfigLoader.load()
            self.apply_styles()
            self.update_time()
        except Exception as e:
            print(f"Ошибка обновления: {e}")

    def update_time(self):
        fmt = "%H:%M:%S" if self.config['clock'].get('show_seconds', True) else "%H:%M"
        self.label.setText(datetime.now().strftime(fmt))

    # ... методы _enum_windows, set_to_background и cleanup_wallpaper без изменений ...
    def _enum_windows(self, hwnd, l_param):
        shell_dll = ctypes.windll.user32.FindWindowExW(hwnd, 0, "SHELLDLL_DefView", None)
        if shell_dll:
            self.workerw = ctypes.windll.user32.FindWindowExW(0, hwnd, "WorkerW", None)
        return True

    def set_to_background(self):
        hwnd = self.winId().__int__()
        progman = ctypes.windll.user32.FindWindowW("Progman", None)
        ctypes.windll.user32.SendMessageTimeoutW(progman, 0x052C, 0, 0, 0, 1000, None)
        ctypes.windll.user32.EnumWindows(self._enum_windows_callback, 0)
        if self.workerw:
            ctypes.windll.user32.SetParent(hwnd, self.workerw)
        else:
            ctypes.windll.user32.SetParent(hwnd, progman)

    def cleanup_wallpaper(self):
        ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, None, 0x01 | 0x02)

    def update_geometry(self):
        screens = QGuiApplication.screens()
        rect = screens[0].geometry()
        for screen in screens:
            rect = rect.united(screen.geometry())
        self.setGeometry(rect)

if __name__ == "__main__":
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    cfg = ConfigLoader.load()
    wallpaper = LiveWallpaper(cfg)
    
    exit_code = app.exec()
    wallpaper.cleanup_wallpaper()
    sys.exit(exit_code)