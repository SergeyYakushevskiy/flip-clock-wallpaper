from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QFrame


class FlipDigit(QFrame):
    """Виджет одной цифры с эффектом перекидывания"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 160)
        self.current_val = "0"
        self.next_val = "0"

        # Основной лейбл
        self.label = QLabel(self.current_val, self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setGeometry(0, 0, 100, 160)

        # Стилизация под "старый пластик" и Flip-стиль
        self.setStyleSheet("""
            QFrame {
                background-color: #1A1A1A;
                border-radius: 10px;
                color: #DCDCDC;
                border: 2px solid #333;
            }
        """)
        self.font = QFont("Arial Black", 80)  # Flip clock обычно использует жирные гротески
        self.label.setFont(self.font)

    def set_value(self, val):
        if self.current_val != val:
            self.current_val = val
            self.label.setText(val)
            self.animate_flip()

    def animate_flip(self):
        # Простая анимация "подмигивания" при смене цифры
        anim = QPropertyAnimation(self.label, b"geometry")
        anim.setDuration(300)
        anim.setStartValue(QRect(0, 80, 100, 0))  # Схлопывание в центр
        anim.setEndValue(QRect(0, 0, 100, 160))
        anim.setEasingCurve(QEasingCurve.Type.OutBounce)
        anim.start()