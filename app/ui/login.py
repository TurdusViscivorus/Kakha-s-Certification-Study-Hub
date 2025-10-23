"""Authentication dialog for the Study Hub."""
from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from ..services.auth_service import AuthService, AuthenticatedUser
from .. import windows_hello


class LoginDialog(QtWidgets.QDialog):
    authenticated = QtCore.Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Kakha's Study Hub - Sign In")
        self.resize(420, 240)
        self._auth_service = AuthService()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        self.username_edit = QtWidgets.QLineEdit()
        self.password_edit = QtWidgets.QLineEdit()
        self.password_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        form.addRow("Username", self.username_edit)
        form.addRow("Password", self.password_edit)

        layout.addLayout(form)

        self.status_label = QtWidgets.QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        if windows_hello.is_available():
            self.hello_checkbox = QtWidgets.QCheckBox("Require Windows Hello verification")
            layout.addWidget(self.hello_checkbox)
        else:
            self.hello_checkbox = None

        button_layout = QtWidgets.QHBoxLayout()
        self.login_button = QtWidgets.QPushButton("Sign In")
        self.register_button = QtWidgets.QPushButton("Register")
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)
        layout.addLayout(button_layout)

        self.login_button.clicked.connect(self._handle_login)
        self.register_button.clicked.connect(self._handle_register)

    def _handle_login(self) -> None:
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        if not username or not password:
            self.status_label.setText("Please provide both username and password.")
            return
        user = self._auth_service.authenticate(username, password)
        if user:
            if self.hello_checkbox is not None:
                self.hello_checkbox.setChecked(user.hello_enabled)
            if user.hello_enabled and windows_hello.is_available():
                if not windows_hello.request_consent("Authenticate with Windows Hello"):
                    self.status_label.setText("Windows Hello verification failed.")
                    return
            self._persist_hello_choice(user.username)
            self.authenticated.emit(user)
            self.accept()
        else:
            self.status_label.setText("Invalid credentials. Please try again.")

    def _handle_register(self) -> None:
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        if len(password) < 8:
            self.status_label.setText("Password must be at least 8 characters.")
            return
        try:
            user = self._auth_service.register(username, password)
        except ValueError as exc:
            self.status_label.setText(str(exc))
            return
        self._persist_hello_choice(user.username)
        self.authenticated.emit(user)
        self.accept()

    def _persist_hello_choice(self, username: str) -> None:
        if self.hello_checkbox is None:
            return
        self._auth_service.update_windows_hello(username, self.hello_checkbox.isChecked())

