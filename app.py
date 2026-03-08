
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox

from src.config.logger import logger
from src.wallpaper.live_wallpaper import LiveWallpaper


sys.path.append(str(Path(__file__).parent))
if __name__ == "__main__":
    logger.info('запуск живых обоев')
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    try:
        wallpaper = LiveWallpaper()
    except FileNotFoundError as e:
        logger.exception("ошибка запуска конфигурации")

        QMessageBox.critical(
            None,
            "Ошибка запуска",
            str(e)
        )

        sys.exit(1)

    except Exception:
        logger.exception("неизвестная ошибка запуска")

        QMessageBox.critical(
            None,
            "Ошибка запуска",
            "Произошла непредвиденная ошибка.\n"
            "Подробности смотрите в логах."
        )

        sys.exit(1)
    logger.info('живые обои успешно запущены')
    code = app.exec()
    sys.exit(code)