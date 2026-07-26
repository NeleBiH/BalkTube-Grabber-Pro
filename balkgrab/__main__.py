"""Entry point for BalkGrab: python -m balkgrab"""

import sys
import os
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger("BalkGrab")


def main():
    from . import APP_NAME, APP_VERSION
    from .constants import ICON_BASE_DIR, ICON_DIR

    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QIcon
    from PySide6.QtCore import QSettings

    log.info("=" * 50)
    log.info(f"{APP_NAME} v{APP_VERSION} - Starting...")
    log.info("=" * 50)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("BalkGrab")
    app.setDesktopFileName("balkgrab")

    icon_path = os.path.join(ICON_BASE_DIR, ICON_DIR, "icon_256x256.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    from .app import BalkGrabGrabber
    window = BalkGrabGrabber()

    settings = QSettings("BalkGrab", "BalkGrab")
    if settings.value("start_minimized", False, type=bool):
        window.hide()
    else:
        window.show()

    log.info("Application started!")
    log.info("-" * 50)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
