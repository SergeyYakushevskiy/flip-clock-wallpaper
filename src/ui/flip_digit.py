import math

from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty, QEasingCurve
from PyQt6.QtGui import QFont, QFontDatabase, QPainter, QPixmap, QColor, QLinearGradient
from PyQt6.QtWidgets import QWidget

from src.exception.font_load_exception import FontLoadException
from src.config.paths import FONTS_DIR
from src.config.logger import logger

class FlipDigit(QWidget):

    _digit_cache_pool = {}
    _plate_cache_pool = {}

    def __init__(self, font_name, font_size, font_color, font_style="", parent=None):
        super().__init__(parent)

        self.current_val = "0"
        self.next_val = "0"
        self._flip_progress = 1.0

        self.font_color = QColor(font_color)
        self.apply_font(font_name, font_size, font_style)

        self.top_shadow = self._render_shadow()
        self.bottom_shadow = self._render_shadow()

        self.anim = QPropertyAnimation(self, b"flip_progress")
        self.anim.setDuration(500)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim.finished.connect(self._on_anim_finished)

    @pyqtProperty(float)
    def flip_progress(self):
        return self._flip_progress

    @flip_progress.setter
    def flip_progress(self, value):
        self._flip_progress = value
        self.update()

    def apply_font(self, font_name=None, font_size=None, font_style=None):
        if font_name:
            self.font_name = font_name
            try:
                self._load_custom_font(font_name)
            except FontLoadException as e:
                logger.debug(e.message)
        if font_size:
            self.font_size = font_size
        if font_style is not None:
            self.font_style = font_style.lower()

        italic_factor = 1.2 if "italic" in self.font_style else 1.0
        self.w = int(self.font_size * italic_factor)
        self.h = int(self.font_size * 1.6)
        self.half_h = self.h // 2
        self.setFixedSize(self.w, self.h)

        self.font = QFont(self.font_name, self.font_size)
        self.font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        self.font.setBold("bold" in self.font_style)
        self.font.setItalic("italic" in self.font_style)

        cache_key = (self.font_name, self.font_size, self.font_color.name(), self.font_style)

        if cache_key not in FlipDigit._plate_cache_pool:
            FlipDigit._plate_cache_pool[cache_key] = self._render_base_plate()
        self.base_plate = FlipDigit._plate_cache_pool[cache_key]

        if cache_key not in FlipDigit._digit_cache_pool:
            FlipDigit._digit_cache_pool[cache_key] = self._generate_digit_cache()
        self.digit_cache = FlipDigit._digit_cache_pool[cache_key]

        self.curr_pixmap = self.digit_cache.get(self.current_val, self.base_plate)
        self.next_pixmap = self.digit_cache.get(self.next_val, self.base_plate)

        self.update()

    def set_value(self, val):
        if self.current_val == val:
            return
        self.next_val = val
        self.next_pixmap = self.digit_cache[val]
        self.anim.stop()
        self.anim.start()

    def _on_anim_finished(self):
        self.current_val = self.next_val
        self.curr_pixmap = self.next_pixmap

    def _load_custom_font(self, font_name):
        if not FONTS_DIR.exists():
            return
        # ищем ttf-файлы, имя которых начинается с font_name
        font_files = list(FONTS_DIR.glob(f"{font_name}*.ttf"))
        if not font_files:
            return

        font_id = QFontDatabase.addApplicationFont(str(font_files[0]))
        if font_id == -1:
            raise FontLoadException(f'не удалось загрузить шрифт: {font_name}')

        # Получаем правильное имя шрифта из файла
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            self.font_name = families[0]  # заменяем имя на корректное

    def _render_base_plate(self):
        pixmap = QPixmap(self.w, self.h)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad = QLinearGradient(0, 0, self.w, self.h)
        grad.setColorAt(0, QColor("#3a3a3a"))
        grad.setColorAt(0.15, QColor("#222222"))
        grad.setColorAt(0.85, QColor("#151515"))
        grad.setColorAt(1, QColor("#050505"))
        painter.setBrush(grad)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(
            0,
            0,
            self.w,
            self.h,
            self.w / 12,
            self.w / 12
        )
        painter.end()
        return pixmap

    def _generate_digit_cache(self):
        cache = {}
        for d in "0123456789":
            cache[d] = self._render_digit_surface(d)
        return cache

    def _render_digit_surface(self, text):
        pixmap = QPixmap(self.base_plate)
        painter = QPainter(pixmap)
        painter.setFont(self.font)
        painter.setPen(self.font_color)
        rect = pixmap.rect()
        if self.font.italic():
            extra_width = int(self.font_size * 0.2)
            rect.setWidth(rect.width() - extra_width)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        return pixmap

    def _render_shadow(self):
        shadow = QPixmap(self.w, self.half_h)
        shadow.fill(Qt.GlobalColor.transparent)
        painter = QPainter(shadow)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 150))
        painter.setPen(Qt.PenStyle.NoPen)
        radius = self.w / 12
        painter.drawRoundedRect(0, 0, self.w, self.half_h, radius, radius)
        painter.end()
        return shadow

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        progress = self._flip_progress
        cos_val = math.cos(progress * math.pi)

        # рисуем верхнюю и нижнюю половину
        painter.drawPixmap(0, 0, self.next_pixmap, 0, 0, self.w, self.half_h)
        painter.drawPixmap(0, self.half_h, self.curr_pixmap, 0, self.half_h, self.w, self.half_h)

        # отрисовка тени сверху/снизу
        # вместо текущего блока с shadow
        if 0.0 < progress < 1.0:
            # верхняя и нижняя тени отдельно
            top_alpha = int(max(0, (0.5 - progress) * 2 * 150))  # плавное появление сверху
            bottom_alpha = int(max(0, (progress - 0.5) * 2 * 150))  # плавное появление снизу

            radius = self.w / 12

            # верхняя тень
            if top_alpha > 0:
                painter.setBrush(QColor(0, 0, 0, top_alpha))
                painter.drawRoundedRect(0, 0, self.w, self.half_h, radius, radius)

            # нижняя тень
            if bottom_alpha > 0:
                painter.setBrush(QColor(0, 0, 0, bottom_alpha))
                painter.drawRoundedRect(0, self.half_h, self.w, self.half_h, radius, radius)

        # переворот верхней/нижней половины
        painter.save()
        painter.translate(0, self.half_h)
        if progress < 0.5:
            painter.scale(1, cos_val)
            painter.drawPixmap(0, -self.half_h, self.curr_pixmap, 0, 0, self.w, self.half_h)
        else:
            painter.scale(1, -cos_val)
            painter.drawPixmap(0, 0, self.next_pixmap, 0, self.half_h, self.w, self.half_h)
        painter.restore()

        # простые полоски для светового эффекта
        painter.fillRect(0, self.half_h - 1, self.w, 3, QColor(0, 0, 0, 200))
        painter.fillRect(0, self.half_h + 2, self.w, 1, QColor(255, 255, 255, 30))
