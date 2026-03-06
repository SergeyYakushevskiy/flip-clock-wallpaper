import math
from PyQt6.QtCore import Qt, QPropertyAnimation, pyqtProperty, QEasingCurve
from PyQt6.QtGui import QFont, QFontDatabase, QPainter, QPixmap, QColor, QLinearGradient
from PyQt6.QtWidgets import QWidget
from src.config_loader import ConfigLoader


class FlipDigit(QWidget):
    def __init__(self, font_name="Arial", font_size=80, font_color="#DCDCDC", font_style="", parent=None):
        super().__init__(parent)

        self.current_val = "0"
        self.next_val = "0"
        self._flip_progress = 1.0

        self.font_color = QColor(font_color)
        self.apply_font(font_name, font_size, font_style)

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
            self._load_custom_font(font_name)
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
        if "bold" in self.font_style:
            self.font.setBold(True)
        if "italic" in self.font_style:
            self.font.setItalic(True)

        self.base_plate = self._render_base_plate()
        self.digit_cache = self._generate_digit_cache()
        self.curr_pixmap = self.digit_cache[self.current_val]
        self.next_pixmap = self.digit_cache[self.next_val]
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
        base_dir = ConfigLoader.get_base_dir()
        font_files = list(base_dir.glob(f"assets/fonts/{font_name}*.ttf"))
        if font_files:
            font_id = QFontDatabase.addApplicationFont(str(font_files[0]))
            if font_id == -1:
                print(f"Failed to load font {font_files[0]}")

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
        painter.drawRoundedRect(0, 0, self.w, self.h, self.w / 12, self.w / 12)
        painter.end()

        return pixmap

    def _generate_digit_cache(self):
        return {d: self._render_digit_surface(d) for d in "0123456789"}

    def _render_digit_surface(self, text):
        pixmap = QPixmap(self.base_plate)
        painter = QPainter(pixmap)
        painter.setFont(self.font)
        painter.setPen(self.font_color)

        # Расширяем границы для italic
        rect = pixmap.rect()
        if self.font.italic():
            extra_width = int(self.font_size * 0.2)
            rect.setWidth(rect.width() - extra_width)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        return pixmap

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        progress = self._flip_progress
        angle = progress * math.pi
        cos_val = math.cos(angle)

        painter.drawPixmap(0, 0, self.next_pixmap, 0, 0, self.w, self.half_h)
        painter.drawPixmap(0, self.half_h, self.curr_pixmap, 0, self.half_h, self.w, self.half_h)

        if 0.0 < progress < 1.0:
            shadow_alpha = int((1 - abs(cos_val)) * 150)
            radius = self.w / 12

            rect_y = self.half_h if progress < 0.5 else 0
            rect_height = self.half_h

            painter.setBrush(QColor(0, 0, 0, shadow_alpha))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(0, rect_y, self.w, rect_height, radius, radius)

        painter.save()
        painter.translate(0, self.half_h)

        if progress < 0.5:
            painter.scale(1, cos_val)
            painter.drawPixmap(0, -self.half_h, self.curr_pixmap, 0, 0, self.w, self.half_h)
        else:
            painter.scale(1, -cos_val)
            painter.drawPixmap(0, 0, self.next_pixmap, 0, self.half_h, self.w, self.half_h)

        painter.restore()

        # Разделительная линия
        painter.fillRect(0, self.half_h - 1, self.w, 3, QColor(0, 0, 0, 200))
        painter.fillRect(0, self.half_h + 2, self.w, 1, QColor(255, 255, 255, 30))

