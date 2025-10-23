"""Entry point for Kakha's Certification Study Hub."""
from __future__ import annotations

import sys

from PySide6 import QtWidgets

from .logging_config import configure_logging
from .ui.login import LoginDialog
from .ui.main_window import MainWindow


def main() -> int:
    configure_logging()
    app = QtWidgets.QApplication(sys.argv)
    login = LoginDialog()
    user_container = {}

    def on_authenticated(user):
        user_container["user"] = user

    login.authenticated.connect(on_authenticated)
    if login.exec() != QtWidgets.QDialog.Accepted:
        return 0
    user = user_container.get("user")
    if not user:
        return 0
    window = MainWindow(user)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
