"""Require the published room files to match the reviewed site before CI is green."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

PUBLIC_ROOM_URL = "https://lexoniarus.github.io/aiko-desktop-pet/room/"


def fetch(name: str) -> bytes:
    request = urllib.request.Request(
        PUBLIC_ROOM_URL + name + f"?verify={time.time_ns()}",
        headers={"Cache-Control": "no-cache"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def verify(site: Path) -> None:
    expected = (site / "install.json").read_bytes()
    for attempt in range(12):
        try:
            if fetch("install.json") == expected:
                break
        except (OSError, urllib.error.URLError):
            pass
        if attempt == 11:
            raise RuntimeError(
                "Public update descriptor does not match the reviewed site"
            )
        print("Waiting for the reviewed update descriptor to become public", flush=True)
        time.sleep(10)
    for name in ("index.html", "sw.js"):
        if fetch(name) != (site / name).read_bytes():
            raise RuntimeError(f"Published starter differs: {name}")
    descriptor = json.loads(expected)
    runtime_name: str = descriptor["package"]
    path = (site / runtime_name).resolve()
    if not runtime_name.startswith("packages/") or not path.is_relative_to(
        site.resolve()
    ):
        raise ValueError("Invalid runtime package path")
    published = fetch(runtime_name)
    if len(published) != descriptor["size"] or hashlib.sha256(published).digest() != (
        hashlib.sha256(path.read_bytes()).digest()
    ):
        raise RuntimeError("Published runtime package differs from the reviewed ZIP")
    print(f"Verified live descriptor, starter and runtime: {descriptor['version']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "dist-room/published/room",
    )
    verify(parser.parse_args().site)


if __name__ == "__main__":
    main()
