Param(
    [string]$InstallDir = "$env:USERPROFILE\KakhaStudyHub"
)

$ErrorActionPreference = "Stop"

function Invoke-ExternalCommand {
    param (
        [string]$Executable,
        [string[]]$Arguments,
        [string]$ErrorMessage
    )

    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw [System.Exception]::new($ErrorMessage)
    }
}

Write-Host "== Kakha's Certification Study Hub installer =="

function Get-CommandPath {
    param(
        [System.Management.Automation.CommandInfo]$Command
    )

    if ($null -ne $Command) {
        if ($Command.Source) { return $Command.Source }
        if ($Command.Path) { return $Command.Path }
        if ($Command.Definition) { return $Command.Definition }
    }

    return $null
}

function Get-CompatiblePython {
    $pythonLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pythonLauncher) {
        foreach ($requestedVersion in @("3.12", "3.11")) {
            $versionOutput = & py -$requestedVersion -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null
            if ($LASTEXITCODE -eq 0 -and $versionOutput) {
                $executable = & py -$requestedVersion -c "import sys; print(sys.executable)" 2>$null
                if ($executable -and (Test-Path $executable)) {
                    return [PSCustomObject]@{ Version = [Version]$versionOutput.Trim(); Executable = $executable.Trim() }
                }
            }
        }
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    $pythonPath = Get-CommandPath $pythonCmd
    if ($pythonPath) {
        $versionOutput = & $pythonPath -c "import sys; print('.'.join(map(str, sys.version_info[:3])))" 2>$null
        if ($LASTEXITCODE -eq 0 -and $versionOutput) {
            $version = [Version]$versionOutput.Trim()
            if ($version -ge [Version]"3.11" -and $version -lt [Version]"3.13") {
                return [PSCustomObject]@{ Version = $version; Executable = $pythonPath }
            }
        }
    }

    return $null
}

function Ensure-CompatiblePython {
    Write-Host "Checking Python version..."
    $pythonInfo = Get-CompatiblePython
    if ($pythonInfo) {
        return $pythonInfo
    }

    $winget = Get-Command winget -ErrorAction SilentlyContinue
    $wingetPath = Get-CommandPath $winget
    if ($wingetPath) {
        Write-Host "Python 3.11/3.12 not found. Attempting to install Python 3.12 via winget..."
        try {
            & $wingetPath install -e --id Python.Python.3.12 --scope=CurrentUser --accept-package-agreements --accept-source-agreements
        }
        catch {
            Write-Warning "winget install failed: $($_.Exception.Message)"
        }

        $pythonInfo = Get-CompatiblePython
        if ($pythonInfo) {
            return $pythonInfo
        }
    }

    throw "Compatible Python interpreter not found. Please install 64-bit Python 3.11 or 3.12 and rerun the installer."
}

$pythonInfo = Ensure-CompatiblePython
Write-Host "Using Python $($pythonInfo.Version.ToString()) at $($pythonInfo.Executable)"

if (-Not (Test-Path $InstallDir)) {
    New-Item -ItemType Directory -Path $InstallDir | Out-Null
}

Write-Host "Creating virtual environment..."
& $pythonInfo.Executable -m venv "$InstallDir\venv"
$venvPython = Join-Path $InstallDir "venv\Scripts\python.exe"

Write-Host "Installing dependencies..."
$projectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$requirementsPath = Join-Path $projectRoot "requirements.txt"
Invoke-ExternalCommand -Executable $venvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip") -ErrorMessage "Failed to upgrade pip."
Invoke-ExternalCommand -Executable $venvPython -Arguments @("-m", "pip", "install", "-r", $requirementsPath) -ErrorMessage "Failed to install required Python packages."
Invoke-ExternalCommand -Executable $venvPython -Arguments @("-m", "pip", "install", "pyinstaller") -ErrorMessage "Failed to install PyInstaller."

$venvVersionString = (& $venvPython -c "import sys; print('.'.join(map(str, sys.version_info[:3])))").Trim()
$venvVersion = [Version]$venvVersionString
$isWindowsPlatform = [System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT
if ($isWindowsPlatform) {
    if ($venvVersion.Major -eq 3 -and $venvVersion.Minor -eq 11) {
        try {
            Invoke-ExternalCommand -Executable $venvPython -Arguments @("-m", "pip", "install", "winrt>=1.0") -ErrorMessage "Failed to install Windows Hello dependency 'winrt'."
        }
        catch {
            Write-Warning "Optional Windows Hello dependency installation failed: $($_.Exception.Message)"
        }
    }
    elseif ($venvVersion.Major -eq 3 -and $venvVersion.Minor -ge 12) {
        try {
            Invoke-ExternalCommand -Executable $venvPython -Arguments @("-m", "pip", "install", "winsdk>=1.0") -ErrorMessage "Failed to install Windows Hello dependency 'winsdk'."
        }
        catch {
            Write-Warning "Optional Windows Hello dependency installation failed: $($_.Exception.Message)"
        }
    }
}

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
Invoke-ExternalCommand -Executable $venvPython -Arguments @("-m", "PyInstaller", "run_app.py", "--noconfirm", "--windowed", "--name", "KakhaStudyHub", "--icon", $iconPath) -ErrorMessage "PyInstaller build failed."
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
