# Windows setup

Extract the complete source ZIP to a permanent, writable folder, then
double-click `Aiko_installieren.bat`. Do not run it inside the ZIP viewer.
Setup uses Windows PowerShell 5.1, included in Windows 10/11. It does not
require administrator privileges or change the saved PowerShell execution
policy; the batch file sets the policy for its own setup process only.

## What setup does

1. Require Windows 10/11, then reuse a healthy local `.venv` or find Python
   3.11+ with Tkinter, `venv` and `ensurepip`. Every candidate must create and
   destroy a real hidden Tk window; importing `tkinter` alone is insufficient.
   Windows itself does not include Python or Tcl/Tk.
2. If no working runtime exists, download the full official Python 3.13.16
   installer directly from python.org for x64, x86 or ARM64 Windows. Verify its
   pinned SHA-256 against the [official release checksums](https://www.python.org/downloads/release/python-31316/)
   before executing it. Install for the current user with Tcl/Tk and pip
   explicitly enabled; repair damaged runtime files if necessary. WinGet,
   Microsoft Store and manual package downloads are unnecessary. See the
   [official unattended install options](https://docs.python.org/3.13/using/windows.html#installing-without-ui).
3. Create `.venv` inside the extracted Aiko folder. Only this environment
   receives the packages from [`requirements.txt`](../requirements.txt).
   Currently the file declares **no third-party runtime packages**: the
   application uses Python's standard library and Tkinter. Pillow, Ruff,
   Mypy and Pyright are developer tools, not required by players.
4. Import the application, validate the character catalog and load one
   character PNG in a hidden Tk window. No pet session or save is opened.
5. Create `Aiko Desktop Pet` shortcuts on the current user's desktop and
   under the Start menu's `Aiko Desktop Pet` folder. Setup does not add
   automatic startup, a service or a scheduled task.

Start Aiko with either shortcut or `Aiko_starten.bat`. The normal and debug
launchers prefer `.venv`; a separate activation command is unnecessary.
The extracted source folder is the application location and must remain
in place. Python environments are tied to their location; see the
[Python venv documentation](https://docs.python.org/3.13/library/venv.html).

## Options and troubleshooting

For an explicit Python installation, no Python download, or no shortcuts:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tools\install_windows.ps1 -PythonExecutable "C:\Path to Python\python.exe" -NoPythonInstall -NoShortcuts
```

The explicit interpreter is used when creating a new environment. Existing
healthy environments are reused. An invalid explicit interpreter causes an
error instead of being silently replaced. `-NoPythonInstall` disables runtime
downloads/installations, including repair. Rerunning setup processes requirements
again and refreshes shortcuts; it does not clear progress or configuration.
Use `-ShortcutDirectory "C:\My shortcuts"` instead of `-NoShortcuts` to
create the shortcut in a chosen folder instead of the desktop and Start menu.

- **WinGet or Tcl/Tk missing:** run setup normally. It downloads the full
  Python installer and enables Tcl/Tk automatically. Installing a package
  named `tkinter` with pip will not supply this Python component.
- **Broken `.venv` or moved folder:** close Aiko and rerun setup. Once a
  working base runtime is available, setup renames the old environment to a
  unique `.venv-backup-<timestamp>-<id>` folder and creates a new `.venv`.
  Remove the backup once the new environment works; it is ignored by Git.
- **Older Windows:** versions below Windows 10 are rejected before downloads.
  Supporting those systems requires a separate compatibility baseline.
- **Setup reports an error:** its window stays open with the failing step.
  Aiko's `Aiko_starten_debug.bat` keeps application errors visible.
- **Offline use:** with suitable Python already installed, the present empty
  runtime requirements need no package downloads. Installing Python or future
  dependencies requires network access.

## Removal

Close Aiko, delete its desktop shortcut and Start menu `Aiko Desktop Pet`
folder, then delete the extracted Aiko folder (including `.venv`). Python
is a separate shared installation; uninstall it through Windows settings
only if you no longer need it for other applications.

Progress remains at `%LOCALAPPDATA%\AikoDesktopPet\state.sqlite3`, or the
configured `AIKO_SAVE_PATH`. Setup and removal do not intentionally alter
that file. If you configured a save inside the extracted source folder,
move it elsewhere before deleting that folder.

SQLite progress is created locally by Python's standard library; setup does not
ship a populated database or require a database server. On the first updated
application start, supported old JSON is backed up and imported. Existing
`.json` overrides select a same-stem SQLite save. See [data and saves](DATA_AND_SAVES.md)
for strict import, errors and backup/restore rules.
