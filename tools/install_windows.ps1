# Compatible with the Windows PowerShell 5.1 shipped with Windows 10/11.
[CmdletBinding()]
param(
    [string]$PythonExecutable,
    [switch]$NoPythonInstall,
    [switch]$NoShortcuts,
    [string]$ShortcutDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$environmentPath = Join-Path $repositoryRoot '.venv'
$environmentPython = Join-Path $environmentPath 'Scripts\python.exe'

function Get-CompatiblePython {
    param([string]$Command, [string[]]$PrefixArguments = @())
    # A rejected candidate must not abort discovery (e.g. an old Python or alias).
    try {
        $probe = 'import sys, tkinter as tk, venv, ensurepip; assert sys.version_info >= (3, 11); root = tk.Tk(); root.withdraw(); root.update_idletasks(); root.destroy(); print(sys.executable)'
        $result = & $Command @PrefixArguments -c $probe 2>$null
        if ($LASTEXITCODE -eq 0 -and $result) {
            $executable = ([string]($result | Select-Object -Last 1)).Trim()
            if (Test-Path -LiteralPath $executable -PathType Leaf) {
                return $executable
            }
        }
    } catch {
        # Missing Tcl/Tk, an unsupported version or a missing command: try next.
    }
    return $null
}

function Get-PythonDownload {
    param([string]$Architecture)
    # Full installers include Tcl/Tk; the embeddable distribution does not.
    # SHA-256 values from https://www.python.org/downloads/release/python-31316/
    $version = '3.13.16'
    switch ($Architecture.ToUpperInvariant()) {
        'AMD64' {
            $suffix = '-amd64'
            $checksum = 'fb4f9f5d438b2396da0086dc70b935c530cb578e37adc6d354f7ad2037fee83b'
        }
        'X86' {
            $suffix = ''
            $checksum = '394ca84150ea428db952cb617c1163c49fbc30e47ec53048c26e6ae44265df07'
        }
        'ARM64' {
            $suffix = '-arm64'
            $checksum = '696e2226062c6ec3622c13f143d28336a856968518e49cb4f4c62513215a4f5d'
        }
        default { throw "Nicht unterstuetzte Windows-Architektur: $Architecture" }
    }
    return [pscustomobject]@{
        Url = "https://www.python.org/ftp/python/$version/python-$version$suffix.exe"
        Sha256 = $checksum
    }
}

function Install-PythonWithTk {
    $architecture = $env:PROCESSOR_ARCHITEW6432
    if (-not $architecture) { $architecture = $env:PROCESSOR_ARCHITECTURE }
    $download = Get-PythonDownload $architecture
    $temporaryFolder = Join-Path ([IO.Path]::GetTempPath()) ('Aiko-python-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $temporaryFolder | Out-Null
    $installer = Join-Path $temporaryFolder 'python-setup.exe'
    try {
        Write-Host 'Lade den offiziellen Python-Installer inklusive Tcl/Tk herunter ...'
        $previousProtocol = [Net.ServicePointManager]::SecurityProtocol
        try {
            [Net.ServicePointManager]::SecurityProtocol = $previousProtocol -bor [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $download.Url -OutFile $installer -UseBasicParsing -TimeoutSec 180
        } finally {
            [Net.ServicePointManager]::SecurityProtocol = $previousProtocol
        }
        if ((Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash -ne $download.Sha256) {
            throw 'Die Pruefsumme des Python-Downloads stimmt nicht. Der Installer wird nicht ausgefuehrt.'
        }
        Write-Host 'Installiere Python mit Tcl/Tk fuer dieses Windows-Benutzerkonto ...'
        $arguments = @(
            '/quiet', '/norestart', 'InstallAllUsers=0', 'Include_tcltk=1',
            'Include_pip=1', 'Include_exe=1', 'Include_lib=1',
            'Include_launcher=0', 'InstallLauncherAllUsers=0'
        )
        $process = Start-Process -FilePath $installer -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru
        if ($process.ExitCode -notin @(0, 3010)) {
            throw "Python-Installation fehlgeschlagen (Code $($process.ExitCode))."
        }
        $python = Find-CompatiblePython
        if (-not $python) {
            # Maintenance adds missing Tcl/Tk; repair also restores damaged files.
            Write-Host 'Repariere die Python-/Tcl-/Tk-Laufzeit ...'
            $process = Start-Process -FilePath $installer -ArgumentList (@('/repair') + $arguments) -WindowStyle Hidden -Wait -PassThru
            if ($process.ExitCode -notin @(0, 3010)) {
                throw "Python-Reparatur fehlgeschlagen (Code $($process.ExitCode))."
            }
            $python = Find-CompatiblePython
        }
        if (-not $python) {
            throw 'Python/Tcl/Tk ist nach der Einrichtung nicht startbar. Falls Windows einen Neustart verlangt, bitte neu starten und die Einrichtung wiederholen.'
        }
        return $python
    } finally {
        # Only remove the known file and the empty directory created above.
        if (Test-Path -LiteralPath $installer) { Remove-Item -LiteralPath $installer -Force }
        Remove-Item -LiteralPath $temporaryFolder
    }
}

function Find-CompatiblePython {
    $launcher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($launcher) {
        $candidate = Get-CompatiblePython $launcher.Source @('-3')
        if ($candidate) { return $candidate }
    }
    # Maintenance can repair Python installed in a custom location.
    foreach ($key in @('HKCU:\Software\Python\PythonCore', 'HKLM:\Software\Python\PythonCore', 'HKLM:\Software\WOW6432Node\Python\PythonCore')) {
        foreach ($version in @(Get-ChildItem -LiteralPath $key -ErrorAction SilentlyContinue)) {
            $installKey = Get-Item -LiteralPath ($version.PSPath + '\InstallPath') -ErrorAction SilentlyContinue
            if ($installKey) {
                $executable = $installKey.GetValue('ExecutablePath')
                if (-not $executable -and $installKey.GetValue('')) {
                    $executable = Join-Path $installKey.GetValue('') 'python.exe'
                }
                if ($executable) {
                    $candidate = Get-CompatiblePython $executable
                    if ($candidate) { return $candidate }
                }
            }
        }
    }
    # Also find a newly installed Python before PATH/launcher refreshes.
    $pythonRoots = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python'),
        $env:ProgramFiles
    )
    foreach ($pythonRoot in $pythonRoots) {
        foreach ($directory in @(Get-ChildItem -LiteralPath $pythonRoot -Directory -Filter 'Python3*' -ErrorAction SilentlyContinue | Sort-Object Name -Descending)) {
            $candidate = Get-CompatiblePython (Join-Path $directory.FullName 'python.exe')
            if ($candidate) { return $candidate }
        }
    }
    $command = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($command -and $command.Source -notlike '*\Microsoft\WindowsApps\*') {
        return Get-CompatiblePython $command.Source
    }
    return $null
}

function Invoke-AikoSetup {
    if ($env:OS -ne 'Windows_NT') { throw 'Diese Einrichtung ist fuer Windows 10/11.' }
    $windows = Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    if ([int]$windows.CurrentBuildNumber -lt 10240) {
        throw 'Aiko benoetigt Windows 10 oder neuer. Aeltere Windows-Versionen werden nicht unterstuetzt.'
    }
    foreach ($requiredFile in @('requirements.txt', 'Aiko_Pet.pyw', 'aiko_pet\__main__.py')) {
        if (-not (Test-Path -LiteralPath (Join-Path $repositoryRoot $requiredFile) -PathType Leaf)) {
            throw 'Bitte zuerst den gesamten Aiko-Quellordner entpacken, dann Aiko_installieren.bat starten.'
        }
    }

    if (-not (Get-CompatiblePython $environmentPython)) {
        if ($PythonExecutable) {
            $python = Get-CompatiblePython $PythonExecutable
            if (-not $python) { throw 'Das angegebene Python benoetigt Version 3.11+ mit Tkinter und venv.' }
        } else {
            $python = Find-CompatiblePython
        }
        if (-not $python) {
            if ($NoPythonInstall) { throw 'Kein Python 3.11+ mit Tkinter und venv gefunden.' }
            $python = Install-PythonWithTk
        }
        if (Test-Path -LiteralPath $environmentPath) {
            $backup = '.venv-backup-' + [DateTime]::UtcNow.ToString('yyyyMMddTHHmmss') + '-' + [guid]::NewGuid().ToString('N')
            Rename-Item -LiteralPath $environmentPath -NewName $backup
            Write-Host "Unbrauchbare .venv als $backup gesichert. Erstelle die Umgebung neu ..."
        }
        Write-Host "Verwende Python: $python"
        & $python -m venv $environmentPath
        if ($LASTEXITCODE -ne 0) { throw 'Die lokale Python-Umgebung konnte nicht erstellt werden.' }
    }

    Write-Host 'Pruefe und installiere Laufzeit-Abhaengigkeiten ...'
    & $environmentPython -m pip install --disable-pip-version-check --requirement (Join-Path $repositoryRoot 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Die Installation der Laufzeit-Abhaengigkeiten ist fehlgeschlagen.' }

    Push-Location -LiteralPath $repositoryRoot
    try {
        # No pet instance, settings or save is opened by this smoke check.
        $smokeCheck = @'
import tkinter as tk
import aiko_pet.gui
from aiko_pet.infrastructure.character_assets import load_character_catalog
catalog = load_character_catalog()
root = tk.Tk()
root.withdraw()
try:
    frame = catalog.clips['idle'].frames[0]
    image = tk.PhotoImage(master=root, file=str(frame.file))
finally:
    root.destroy()
'@
        & $environmentPython -c $smokeCheck
        if ($LASTEXITCODE -ne 0) { throw 'Der Starttest fuer Tkinter, Programmdateien oder Bilder ist fehlgeschlagen.' }
    } finally {
        Pop-Location
    }

    $windowlessPython = Join-Path $environmentPath 'Scripts\pythonw.exe'
    if (-not (Test-Path -LiteralPath $windowlessPython -PathType Leaf)) { throw 'pythonw.exe fehlt in der lokalen Umgebung.' }
    if (-not $NoShortcuts) {
        $shell = New-Object -ComObject WScript.Shell
        if ($ShortcutDirectory) {
            $shortcutFolders = @([IO.Path]::GetFullPath($ShortcutDirectory))
        } else {
            $menuFolder = Join-Path ([Environment]::GetFolderPath('Programs')) 'Aiko Desktop Pet'
            $shortcutFolders = @([Environment]::GetFolderPath('DesktopDirectory'), $menuFolder)
        }
        foreach ($folder in $shortcutFolders) {
            New-Item -ItemType Directory -Path $folder -Force | Out-Null
            $shortcut = $shell.CreateShortcut((Join-Path $folder 'Aiko Desktop Pet.lnk'))
            $shortcut.TargetPath = $windowlessPython
            $shortcut.Arguments = '"' + (Join-Path $repositoryRoot 'Aiko_Pet.pyw') + '"'
            $shortcut.WorkingDirectory = $repositoryRoot
            $shortcut.Description = 'Aiko Desktop Pet starten'
            $shortcut.Save()
        }
        Write-Host 'Startverknuepfungen erstellt.'
    }
    Write-Host 'Fertig! Aiko ueber die Verknuepfung oder Aiko_starten.bat starten.'
    Write-Host 'Den entpackten Aiko-Ordner bitte an diesem Ort behalten.'
}

if ($MyInvocation.InvocationName -ne '.') {
    try {
        Invoke-AikoSetup
        exit 0
    } catch {
        Write-Host ("FEHLER: " + $_.Exception.Message) -ForegroundColor Red
        exit 1
    }
}
