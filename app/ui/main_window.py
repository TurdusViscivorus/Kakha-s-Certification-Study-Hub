"""Main application window."""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from ..config import paths
from ..services.analytics_service import AnalyticsService
from ..services.auth_service import AuthenticatedUser
from ..services.content_pack_service import ContentPackService
from ..services.flashcard_service import FlashcardService
from ..services.lab_service import LabService
from ..services.quiz_service import QuizService
from ..importers.anki_importer import AnkiImporter
from ..importers.csv_importer import CSVImporter, TSVImporter
from ..importers.markdown_importer import MarkdownImporter
from ..importers.paste_importer import BulkPasteImporter


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, user: AuthenticatedUser, parent=None) -> None:
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Kakha's Certification Study Hub")
        self.resize(1200, 800)
        self._flashcards = FlashcardService(user.encryption_key)
        self._quiz = QuizService(user.encryption_key)
        self._analytics = AnalyticsService(str(paths.root))
        self._labs = LabService(user.encryption_key)
        self._packs = ContentPackService(user.encryption_key)
        self._setup_ui()

    def _setup_ui(self) -> None:
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self._build_dashboard(), "Dashboard")
        tabs.addTab(self._build_flashcards_tab(), "Flashcards")
        tabs.addTab(self._build_quiz_tab(), "Quizzes")
        tabs.addTab(self._build_labs_tab(), "Labs")
        tabs.addTab(self._build_analytics_tab(), "Analytics")
        tabs.addTab(self._build_packs_tab(), "Content Packs")
        self.setCentralWidget(tabs)

    def _build_dashboard(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        layout.addWidget(QtWidgets.QLabel(f"Welcome, {self.user.username}!"))
        layout.addWidget(QtWidgets.QLabel("All data is encrypted and stored locally."))
        layout.addStretch(1)
        return widget

    # Flashcards
    def _build_flashcards_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        deck_group = QtWidgets.QGroupBox("Decks")
        deck_layout = QtWidgets.QHBoxLayout(deck_group)
        self.deck_name_edit = QtWidgets.QLineEdit()
        deck_layout.addWidget(self.deck_name_edit)
        create_deck_btn = QtWidgets.QPushButton("Create Deck")
        deck_layout.addWidget(create_deck_btn)
        create_deck_btn.clicked.connect(self._create_deck)
        layout.addWidget(deck_group)

        card_group = QtWidgets.QGroupBox("Add Flashcard")
        form = QtWidgets.QFormLayout(card_group)
        self.card_front = QtWidgets.QTextEdit()
        self.card_back = QtWidgets.QTextEdit()
        self.card_type_combo = QtWidgets.QComboBox()
        self.card_type_combo.addItems(["basic", "cloze", "image", "scenario", "command"])
        form.addRow("Front", self.card_front)
        form.addRow("Back", self.card_back)
        form.addRow("Type", self.card_type_combo)
        add_card_btn = QtWidgets.QPushButton("Save Card")
        add_card_btn.clicked.connect(self._add_flashcard)
        form.addRow(add_card_btn)
        layout.addWidget(card_group)

        import_group = QtWidgets.QGroupBox("Import Cards")
        import_layout = QtWidgets.QHBoxLayout(import_group)
        import_btn = QtWidgets.QPushButton("Import File")
        import_btn.clicked.connect(self._import_cards)
        import_layout.addWidget(import_btn)
        paste_btn = QtWidgets.QPushButton("Bulk Paste")
        paste_btn.clicked.connect(self._bulk_paste)
        import_layout.addWidget(paste_btn)
        layout.addWidget(import_group)

        self.flashcard_list = QtWidgets.QListWidget()
        layout.addWidget(self.flashcard_list)
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_flashcards)
        layout.addWidget(refresh_btn)
        self._refresh_flashcards()
        return widget

    def _create_deck(self) -> None:
        name = self.deck_name_edit.text().strip()
        if not name:
            return
        self._flashcards.create_deck(self.user.id, name)
        self.deck_name_edit.clear()

    def _add_flashcard(self) -> None:
        content = {
            "front": self.card_front.toPlainText(),
            "back": self.card_back.toPlainText(),
            "created": dt.datetime.utcnow().isoformat(),
        }
        self._flashcards.create_flashcard(
            user_id=self.user.id,
            deck_id=None,
            card_type=self.card_type_combo.currentText(),
            content=content,
        )
        self.card_front.clear()
        self.card_back.clear()
        self._refresh_flashcards()

    def _refresh_flashcards(self) -> None:
        self.flashcard_list.clear()
        for card in self._flashcards.list_flashcards(self.user.id):
            item = QtWidgets.QListWidgetItem(f"[{card.card_type}] {card.content.get('front', '')}")
            item.setData(QtCore.Qt.UserRole, card)
            self.flashcard_list.addItem(item)

    def _import_cards(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Import Flashcards", str(Path.home()), "Data Files (*.csv *.tsv *.md *.apkg)"
        )
        if not path:
            return
        importer = None
        extension = Path(path).suffix.lower()
        if extension == ".csv":
            importer = CSVImporter()
        elif extension == ".tsv":
            importer = TSVImporter()
        elif extension == ".md":
            importer = MarkdownImporter()
        elif extension == ".apkg":
            importer = AnkiImporter()
        if importer is None:
            QtWidgets.QMessageBox.warning(self, "Unsupported", "Unsupported file format.")
            return
        cards = list(importer.load(Path(path)))
        count = self._flashcards.bulk_import(user_id=self.user.id, cards=cards)
        QtWidgets.QMessageBox.information(self, "Import Complete", f"Imported {count} cards")
        self._refresh_flashcards()

    def _bulk_paste(self) -> None:
        text, ok = QtWidgets.QInputDialog.getMultiLineText(
            self, "Bulk Paste", "Enter one card per line using front::back format"
        )
        if not ok or not text.strip():
            return
        importer = BulkPasteImporter(text)
        cards = list(importer.load(Path("/dev/null")))
        count = self._flashcards.bulk_import(user_id=self.user.id, cards=cards)
        QtWidgets.QMessageBox.information(self, "Import Complete", f"Imported {count} cards")
        self._refresh_flashcards()

    # Quizzes
    def _build_quiz_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        blueprint_btn = QtWidgets.QPushButton("Create CISSP Blueprint")
        blueprint_btn.clicked.connect(self._create_default_blueprint)
        layout.addWidget(blueprint_btn)

        add_question_btn = QtWidgets.QPushButton("Add Question from Card")
        add_question_btn.clicked.connect(self._add_question_from_card)
        layout.addWidget(add_question_btn)

        self.quiz_result_label = QtWidgets.QLabel("No quiz attempts yet.")
        layout.addWidget(self.quiz_result_label)

        take_quiz_btn = QtWidgets.QPushButton("Take Quick Quiz")
        take_quiz_btn.clicked.connect(self._take_quiz)
        layout.addWidget(take_quiz_btn)
        layout.addStretch(1)
        return widget

    def _create_default_blueprint(self) -> None:
        sections = [
            ("Security and Risk Management", 0.15),
            ("Asset Security", 0.10),
            ("Security Architecture", 0.13),
        ]
        blueprint_id = self._quiz.add_blueprint(
            user_id=self.user.id,
            name="CISSP Default",
            description="Standard CISSP weights",
            metadata={"exam": "CISSP"},
            sections=sections,
        )
        QtWidgets.QMessageBox.information(self, "Blueprint", f"Created blueprint #{blueprint_id}")

    def _add_question_from_card(self) -> None:
        cards = self._flashcards.list_flashcards(self.user.id)
        if not cards:
            QtWidgets.QMessageBox.information(self, "No Cards", "Create flashcards first.")
            return
        card = cards[0]
        question_id = self._quiz.add_question(
            user_id=self.user.id,
            blueprint_section_id=None,
            question_type="short",
            prompt={"text": card.content.get("front", "")},
            answer={"text": card.content.get("back", "")},
            explanation={"text": "Derived from flashcard."},
            references=["User Notes"],
            metadata={"section": "Security and Risk Management"},
        )
        QtWidgets.QMessageBox.information(self, "Question", f"Created question #{question_id}")

    def _take_quiz(self) -> None:
        questions = self._quiz.list_questions(self.user.id)
        if not questions:
            QtWidgets.QMessageBox.information(self, "No Questions", "Add questions first.")
            return
        selected = self._quiz.generate_exam(
            user_id=self.user.id,
            blueprint_id=None,
            mode="practice",
            question_pool=questions,
            count=5,
            weights={"Security and Risk Management": 0.2},
        )
        responses = []
        for question in selected:
            answer, ok = QtWidgets.QInputDialog.getText(self, "Quiz", question.prompt.get("text", ""))
            if not ok:
                continue
            responses.append(
                {
                    "question_id": question.id,
                    "question_type": question.question_type,
                    "answer": question.answer.get("text") or question.answer,
                    "user_answer": answer,
                    "confidence": 3,
                }
            )
        if not responses:
            return
        result = self._quiz.grade_attempt(
            user_id=self.user.id,
            blueprint_id=None,
            mode="practice",
            responses=responses,
        )
        self.quiz_result_label.setText(f"Last Score: {result.score:.1f}%")

    # Labs
    def _build_labs_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        self.lab_name_edit = QtWidgets.QLineEdit()
        layout.addWidget(self.lab_name_edit)
        create_lab_btn = QtWidgets.QPushButton("Create Checklist")
        create_lab_btn.clicked.connect(self._create_lab)
        layout.addWidget(create_lab_btn)

        self.labs_list = QtWidgets.QListWidget()
        layout.addWidget(self.labs_list)
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_labs)
        layout.addWidget(refresh_btn)
        self._refresh_labs()
        return widget

    def _create_lab(self) -> None:
        name = self.lab_name_edit.text().strip()
        if not name:
            return
        self._labs.create_checklist(self.user.id, name, "")
        self.lab_name_edit.clear()
        self._refresh_labs()

    def _refresh_labs(self) -> None:
        self.labs_list.clear()
        for checklist in self._labs.list_checklists(self.user.id):
            item = QtWidgets.QListWidgetItem(f"{checklist['name']} ({len(checklist['tasks'])} tasks)")
            self.labs_list.addItem(item)

    # Analytics
    def _build_analytics_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        generate_btn = QtWidgets.QPushButton("Generate Analytics")
        generate_btn.clicked.connect(self._generate_analytics)
        layout.addWidget(generate_btn)
        self.analytics_image = QtWidgets.QLabel()
        self.analytics_image.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.analytics_image)
        return widget

    def _generate_analytics(self) -> None:
        summary = self._analytics.generate_summary(self.user.id)
        pixmap = QtGui.QPixmap(summary.heatmap_path)
        self.analytics_image.setPixmap(pixmap.scaled(600, 200, QtCore.Qt.KeepAspectRatio))

    # Content Packs
    def _build_packs_tab(self) -> QtWidgets.QWidget:
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        install_btn = QtWidgets.QPushButton("Install Pack")
        install_btn.clicked.connect(self._install_pack)
        layout.addWidget(install_btn)
        export_btn = QtWidgets.QPushButton("Export First Pack")
        export_btn.clicked.connect(self._export_pack)
        layout.addWidget(export_btn)
        self.packs_list = QtWidgets.QListWidget()
        layout.addWidget(self.packs_list)
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_packs)
        layout.addWidget(refresh_btn)
        self._refresh_packs()
        return widget

    def _install_pack(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Install Pack", str(Path.home()), "Pack (*.zip *.apkg)")
        if not path:
            return
        info = self._packs.install_pack(self.user.id, Path(path))
        QtWidgets.QMessageBox.information(self, "Pack", f"Installed {info.name} v{info.version}")
        self._refresh_packs()

    def _refresh_packs(self) -> None:
        self.packs_list.clear()
        for pack in self._packs.list_packs(self.user.id):
            item = QtWidgets.QListWidgetItem(f"{pack.name} v{pack.version}")
            item.setToolTip(json.dumps(pack.metadata, indent=2))
            self.packs_list.addItem(item)

    def _export_pack(self) -> None:
        packs = self._packs.list_packs(self.user.id)
        if not packs:
            QtWidgets.QMessageBox.information(self, "No Packs", "Install a pack first.")
            return
        dest, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export Pack", str(Path.home() / "pack.zip"), "Zip (*.zip)")
        if not dest:
            return
        self._packs.export_pack(self.user.id, packs[0].id, Path(dest))
        QtWidgets.QMessageBox.information(self, "Export", "Pack exported successfully.")

