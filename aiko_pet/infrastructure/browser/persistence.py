"""Publish SQLite on IDBFS without requiring an unavailable hard-link syscall."""

from __future__ import annotations

from pathlib import Path

from ...application.storage_contracts import StorageError, StorageFailureKind


def publish_browser_database(source: Path, destination: Path) -> None:
    """The browser holds the exclusive save lock across startup and syncfs.

    An incomplete MEMFS publication is never acknowledged to IndexedDB. Subsequent
    writes retain SQLite's revision guard. Desktop publication stays unchanged.
    """
    try:
        with destination.open("xb") as output, source.open("rb") as incoming:
            while chunk := incoming.read(1024 * 1024):
                output.write(chunk)
    except FileExistsError as error:
        raise StorageError(
            StorageFailureKind.STALE_REVISION, destination,
            "Another browser session already initialized the checkpoint",
        ) from error
    except OSError:
        destination.unlink(missing_ok=True)
        raise
