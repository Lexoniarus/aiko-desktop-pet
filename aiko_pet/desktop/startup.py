"""Stop failed storage restoration before opening a fresh desktop session."""

from collections.abc import Callable
from tkinter import messagebox
from typing import Protocol

from ..application.runtime_resources import PreparedRuntimeResources
from ..application.storage_contracts import StorageError
from ..infrastructure.runtime_dependencies import (
    RuntimeDependencyError,
    prepare_runtime_resources,
)
from ..pet.content import GERMAN_TEXT


class DesktopApplication(Protocol):
    def run(self) -> None: ...


def run_desktop(
    create: Callable[[PreparedRuntimeResources], DesktopApplication],
) -> None:
    """Report a failed restore, without retrying or replacing the selected save."""
    try:
        resources = prepare_runtime_resources()
        app = create(resources)
    except RuntimeDependencyError as error:
        messagebox.showerror(GERMAN_TEXT.format("ui.application_name"), str(error))
        raise SystemExit(1) from error
    except StorageError as error:
        messagebox.showerror(
            GERMAN_TEXT.format("ui.application_name"),
            GERMAN_TEXT.format("ui.load_failed", failure=str(error)),
        )
        raise SystemExit(1) from error
    app.run()
