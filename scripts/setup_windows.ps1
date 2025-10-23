Param(
    [string]$InstallDir = "$env:USERPROFILE\KakhaStudyHub"
)

$ErrorActionPreference = "Stop"

Write-Host "== Kakha's Certification Study Hub installer =="

Write-Host "Checking Python version..."
$pythonVersionString = & python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))"
if (-Not $pythonVersionString) {
    throw "Python interpreter not found. Please install Python 3.11 or 3.12 (64-bit) and rerun the installer."
}

$pythonVersion = [Version]$pythonVersionString
if ($pythonVersion -lt [Version]"3.11" -or $pythonVersion -ge [Version]"3.13") {
    throw "Python $pythonVersionString detected. Install Python 3.11 or 3.12 (64-bit) before running setup_windows.ps1 so that PySide6 and PyInstaller can be installed."
}

if (-Not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
}

Write-Host "Creating virtual environment..."
python -m venv "$InstallDir\venv"
$venvPython = Join-Path $InstallDir "venv\Scripts\python.exe"

Write-Host "Installing dependencies..."
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$requirementsPath = Join-Path $projectRoot "requirements.txt"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r $requirementsPath pyinstaller

Write-Host "Copying application files..."
Copy-Item -Recurse -Force (Join-Path $projectRoot "app") $InstallDir
Copy-Item -Force (Join-Path $projectRoot "run_app.py") $InstallDir
Copy-Item -Force $requirementsPath $InstallDir
Copy-Item -Recurse -Force (Join-Path $projectRoot "assets") $InstallDir

$assetDir = Join-Path $InstallDir "assets"
$iconBase64Path = Join-Path $assetDir "kakha_icon_base64.txt"
$iconPath = Join-Path $assetDir "kakha.ico"
if (-Not (Test-Path $iconPath)) {
    Write-Host "Generating application icon..."
    $iconBytes = [Convert]::FromBase64String((Get-Content $iconBase64Path -Raw))
    [IO.File]::WriteAllBytes($iconPath, $iconBytes)
}

Write-Host "Building Windows executable..."
Push-Location $InstallDir
& $venvPython -m PyInstaller run_app.py --noconfirm --windowed --name "KakhaStudyHub" --icon $iconPath
Pop-Location

$exePath = Join-Path $InstallDir "dist\KakhaStudyHub\KakhaStudyHub.exe"
if (-Not (Test-Path $exePath)) {
    throw "Build failed: $exePath not found."
}

Write-Host "Creating desktop shortcut..."
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "Kakha's Certification Study Hub.lnk"
$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = Split-Path $exePath
$shortcut.IconLocation = $iconPath
$shortcut.Save()

Write-Host "Installation complete. Launching application..."
Start-Process $exePath
