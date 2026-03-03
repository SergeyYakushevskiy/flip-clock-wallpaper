# Live Wallpaper Clock

Живые обои для Windows с цифровыми часами.

## Возможности

- Отображение текущего времени
- Смена дизайна живых обоев
- Пользовательская конфигурация через `config.json`

## Скриншот

![Screenshot](screenshots/screen1.jpg)

## Технологии

- Python 3.x
- PyQt6
- ctypes
- PyInstaller (для создания исполняемого файла)
- Inno Setup (для сборки установщика)

## Установка

### Вариант 1 — готовый установщик
Скачать `.exe` из раздела Releases и установить.

### Вариант 2 — запуск из исходников

```bash
git clone https://github.com/yourname/live-wallpaper-clock.git
cd live-wallpaper-clock
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Произведите установку шрифта Digital-7.tff из бабки assets, после чего можете запустить проект

```bash
python src/app.py
```