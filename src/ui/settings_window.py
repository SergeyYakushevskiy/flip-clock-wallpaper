import json

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QComboBox, QSpinBox, QPushButton, QColorDialog, QCheckBox, QSpacerItem, QSizePolicy,
    QRadioButton, QButtonGroup
)

from src.config.paths import USER_CONFIG_FILE, ICONS_DIR
from src.config.settings_meta import SettingsMeta


class SettingsWindow(QWidget):
    def __init__(self, config, parent):
        super().__init__(None)
        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setWindowTitle("Настройки живых обоев")
        self.config = config.copy()           # текущий конфиг для редактирования
        self.original_config = config.copy()  # для отмены изменений
        self.parent = parent

        icon_path = ICONS_DIR / "app_icon.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.widgets_map = {}  # ключ: (группа, параметр) -> виджет
        self.init_ui()

    def init_ui(self):
        # Основной вертикальный layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)  # внешние отступы
        layout.setSpacing(15)  # расстояние между группами
        self.setLayout(layout)

        # Создаём группы настроек
        for group_name, group_data in self.config.items():
            group_box = QGroupBox(group_name.capitalize())
            group_box.setStyleSheet("QGroupBox { font-weight: bold; }")
            group_layout = QFormLayout()
            group_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)  # метки слева
            group_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)  # виджеты справа
            group_layout.setHorizontalSpacing(15)
            group_layout.setVerticalSpacing(10)
            group_box.setLayout(group_layout)
            layout.addWidget(group_box)

            for key, value in group_data.items():
                widget = self.create_widget(group_name, key, value)
                if widget:
                    self.widgets_map[(group_name, key)] = widget
                    label_text = getattr(SettingsMeta, "KEY_LABEL_MAP", {}).get(key, key)
                    label = QLabel(label_text + ":")
                    label.setAlignment(Qt.AlignmentFlag.AlignLeft)
                    # Оборачиваем виджет в контейнер с правым выравниванием
                    widget_container = QWidget()
                    container_layout = QHBoxLayout()
                    container_layout.setContentsMargins(0, 0, 0, 0)
                    container_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
                    container_layout.addWidget(widget)
                    widget_container.setLayout(container_layout)

                    group_layout.addRow(label, widget_container)

        # Разделитель между настройками и кнопками
        layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()  # выравнивание кнопок вправо

        ok_btn = QPushButton("ОК")
        ok_btn.clicked.connect(self.on_ok)
        apply_btn = QPushButton("Применить")
        apply_btn.clicked.connect(self.on_apply)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.on_cancel)

        buttons_layout.addWidget(ok_btn)
        buttons_layout.addWidget(apply_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

    def create_widget(self, group, key, value):
        if key.endswith("_color"):
            btn = QPushButton()
            btn.setFixedWidth(60)
            btn.setStyleSheet(f"background-color: {value}")
            btn.clicked.connect(lambda _, b=btn: self.pick_color(b))
            return btn

        if key in ("show_seconds"):
            layout = QHBoxLayout()
            cb_true = QRadioButton("Да")
            cb_false = QRadioButton("Нет")

            container = QWidget()
            container.setLayout(layout)

            button_group = QButtonGroup(container)
            button_group.addButton(cb_true)
            button_group.addButton(cb_false)

            layout.addWidget(cb_true)
            layout.addWidget(cb_false)
            if value:
                cb_true.setChecked(True)
            else:
                cb_false.setChecked(True)


            return container

        # Строка со списком шрифтов
        if key == "font_name":
            combo = QComboBox()
            combo.addItems(SettingsMeta.get_fonts())
            combo.setCurrentText(value)
            return combo

        # Числа
        elif key == "font_size":
            spin = QSpinBox()
            spin.setMinimum(SettingsMeta.FONT_SIZE_MIN)
            spin.setMaximum(1000)
            spin.setValue(int(value))
            return spin

        # Стиль шрифта (несколько значений)
        if key == "font_style":
            layout = QHBoxLayout()
            cb_bold = QCheckBox("Жирный")
            cb_italic = QCheckBox("Курсив")
            layout.addWidget(cb_bold)
            layout.addWidget(cb_italic)

            styles = [s.strip() for s in value.lower().split(",") if s.strip()] if value else []
            cb_bold.setChecked("bold" in styles)
            cb_italic.setChecked("italic" in styles)

            container = QWidget()
            container.setLayout(layout)

            return container

        # По умолчанию обычный QLineEdit
        le = QLineEdit(str(value))
        return le

    def pick_color(self, button):
        color = QColorDialog.getColor(QColor(button.palette().button().color()))
        if color.isValid():
            button.setStyleSheet(f"background-color: {color.name()}")

    def apply_changes(self):
        for (group, key), widget in self.widgets_map.items():
            if key.endswith("_color") and isinstance(widget, QPushButton):
                style = widget.styleSheet()
                color = style.split("background-color:")[1].strip()
                self.config[group][key] = color
            elif key == "show_seconds":
                cb_true, _ = widget.findChildren(QRadioButton)
                self.config[group][key] = cb_true.isChecked()
            elif key == "font_name" and isinstance(widget, QComboBox):
                self.config[group][key] = widget.currentText()
            elif key == "font_size" and isinstance(widget, QSpinBox):
                self.config[group][key] = widget.value()
            elif key == "font_style":
                cb_bold, cb_italic = list(widget.findChildren(QCheckBox))
                styles = []
                if cb_bold.isChecked():
                    styles.append("bold")
                if cb_italic.isChecked():
                    styles.append("italic")
                self.config[group][key] = ", ".join(styles)

            # fallback для остальных текстовых полей
            elif isinstance(widget, QLineEdit):
                self.config[group][key] = widget.text()

        with open(USER_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

        # Применяем в родительский LiveWallpaper
        if self.parent:
            self.parent.reload_config()

    def on_ok(self):
        self.apply_changes()
        self.close()

    def on_apply(self):
        self.apply_changes()

    def on_cancel(self):
        self.config = self.original_config.copy()
        self.close()
