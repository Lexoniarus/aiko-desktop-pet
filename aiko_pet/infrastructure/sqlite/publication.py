"""Private temporary databases and atomic first publication without overwrite."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager, suppress
from pathlib import Path

from ...application.storage_contracts import StorageError, StorageFailureKind


@contextmanager
def temporary_database(destination: Path) -> Iterator[Path]:
    descriptor, filename = tempfile.mkstemp(
        prefix=".aiko-",
        suffix=".sqlite3",
        dir=destination.parent,
    )
    os.close(descriptor)
    path = Path(filename)
    try:
        yield path
    finally:
        # Cleanup must not mask a failed write or report a published save as failed.
        with suppress(OSError):
            path.unlink(missing_ok=True)


def publish_database(source: Path, destination: Path) -> None:
    """Both files are on the same filesystem; link creation never replaces a name."""
    try:
        os.link(source, destination)
    except FileExistsError as error:
        raise StorageError(
            StorageFailureKind.STALE_REVISION,
            destination,
            "Another session initialized this save first",
        ) from error
