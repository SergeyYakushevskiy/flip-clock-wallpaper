from PyQt6.QtGui import QFontDatabase

from src.config.paths import FONTS_DIR

class SettingsMeta:
    KEY_LABEL_MAP = {
        "bg_color" : "Цвет фона",
        "font_name" : "Шрифт",
        "font_size" : "Размер панели",
        "font_color" : "Цвет шрифта",
        "font_style" : "Стиль шрифта",
        "show_seconds" : "Секунды"
    }

    FONT_STYLES = ["нормальный", "жирный", "курсив"]
    FONT_SIZE_MIN = 1
    SHOW_SECOND = ["да", "нет"]



    @staticmethod
    def get_fonts():
        system_fonts = QFontDatabase.families()
        custom_fonts = [f.stem for f in FONTS_DIR.glob("*.ttf")]
        return system_fonts + custom_fonts
