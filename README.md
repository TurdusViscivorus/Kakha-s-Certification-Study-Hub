# Kakha's Certification Study Hub

Kakha's Certification Study Hub is a local-first desktop application for Windows that helps you prepare for cybersecurity and AI certifications with encrypted flashcards, quizzes, labs, analytics, and signed content packs.

## Features

- **Secure authentication** – local accounts with Argon2 hashing, encrypted per-user data, optional Windows Hello toggle.
- **Flashcards** – decks, advanced card types, importers for CSV/TSV/Markdown/Anki/. Bulk paste supported.
- **Quizzes & exams** – blueprint-based question banks, multiple question types, exam simulation, scoring and rationale storage.
- **Spaced repetition** – SM-2 scheduling, review logs, daily ramp-up toward exam dates.
- **Progress analytics** – heatmaps, retention curves, radar charts, confidence vs. accuracy scatter, PDF weekly reports.
- **Labs** – track hands-on checklists with encrypted notes and attachments.
- **Content packs** – install and export signed packs mapped to certification objectives.

## Project layout

```
app/
  config.py                # Paths and security configuration
  database.py              # SQLite connection + session management
  models/                  # SQLAlchemy entity definitions
  repositories/            # Data access layers
  services/                # Business logic for each feature area
  ui/                      # PySide6 GUI components
  importers/               # Flashcard import utilities
  main.py                  # GUI entrypoint
run_app.py                 # Convenience launcher script
scripts/setup_windows.ps1  # One-click Windows installer/builder
requirements.txt           # Python dependencies
assets/kakha_icon_base64.txt  # Base64 icon source (installer materializes kakha.ico)
```

## Prerequisites (Windows 11)

- 64-bit Python 3.11 or 3.12 available in `PATH` (PySide6 and PyInstaller do not yet ship wheels for Python 3.13)
- (Optional) Windows Hello support requires the Windows `winrt` package (installed automatically by the setup script)
- PowerShell execution policy that permits running trusted scripts (for example `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`)
- At least 2 GB free disk space for the virtual environment and build artifacts

## One-click installation and launch

1. Download or clone this repository to your Windows machine.
2. Open **PowerShell** and run the bundled script:

   ```powershell
   .\scripts\setup_windows.ps1
   ```

   The script performs the following steps automatically:

   - Creates an isolated virtual environment in `%USERPROFILE%\KakhaStudyHub`
   - Installs Python dependencies and PyInstaller
   - Copies the application files
   - Builds a Windows executable and materializes the custom icon from the bundled Base64 text file
   - Places a desktop shortcut named "Kakha's Certification Study Hub"
   - Launches the application immediately after the build finishes

After the first run you can simply double-click the desktop shortcut (`KakhaStudyHub.exe`) to start studying. All data is saved locally under `%USERPROFILE%\KakhaStudyHub` and encrypted per user.

> **Heads-up:** If the installer reports that your Python version is unsupported, install the latest 64-bit Python 3.11 or 3.12
> release from [python.org](https://www.python.org/downloads/windows/) and re-run the script. PySide6 and PyInstaller are pulled
> in automatically once a supported interpreter is detected.


## Development setup (optional)

If you want to run the GUI without building the executable:

```bash
python -m venv .venv
.\.venv\Scripts\activate  # PowerShell
pip install -r requirements.txt
python run_app.py
```

The application stores user data in `%USERPROFILE%\.kakha_study_hub`. Delete this directory to reset all user accounts and data.

## Testing notes

GUI testing is manual. The repository ships with modular services (`app/services`) that can be unit tested independently if you add your own test harness.
