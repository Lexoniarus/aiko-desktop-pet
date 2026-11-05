"""Download a pinned release artifact; never require private source art in CI."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from zipfile import ZipFile


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    release = json.loads((root / ".room-release.json").read_text("utf8"))
    if (
        set(release) != {"tag", "asset", "sha256"}
        or not re.fullmatch(r"room-test-[\w.-]+", release["tag"])
        or not re.fullmatch(r"aiko-starter-[\w.-]+\.zip", release["asset"])
        or not re.fullmatch(r"[a-f0-9]{64}", release["sha256"])
    ):
        raise ValueError("Invalid room deployment descriptor")
    downloads = root / "dist-room/download"
    downloads.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "gh",
            "release",
            "download",
            release["tag"],
            "--repo",
            "Lexoniarus/aiko-desktop-pet",
            "--pattern",
            release["asset"],
            "--dir",
            str(downloads),
            "--clobber",
        ],
        check=True,
    )
    archive = downloads / release["asset"]
    if hashlib.sha256(archive.read_bytes()).hexdigest() != release["sha256"]:
        raise ValueError("Deployment artifact digest mismatch")
    destination = root / "dist-room/published/room"
    destination.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive) as package:
        for item in package.infolist():
            target = (destination / item.filename).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError("Deployment archive leaves the room directory")
        package.extractall(destination)


if __name__ == "__main__":
    main()
