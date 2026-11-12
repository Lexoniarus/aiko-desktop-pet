"""Install the approved Waiting preview as one shared HD runtime sequence."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from aiko_pet.infrastructure.waiting_assets import WAITING_REST, load_hd_waiting_clip
from aiko_pet.pet.catalog_validation import integer_value, load_json
from tools.character_export_common import (
    HD_FRAME_SIZE,
    load_rgba_component,
    planted_foot_bounds,
    sha256_digest,
)


def export_waiting(source_job: Path, asset_root: Path) -> dict[str, Any]:
    source_job = source_job.resolve()
    timeline = load_json(source_job / "timeline.json")
    rest = (asset_root / WAITING_REST).read_bytes()
    feet = planted_foot_bounds(load_rgba_component(rest))
    rest_digest = sha256_digest(rest)
    files = {WAITING_REST: rest}
    names = {rest_digest: WAITING_REST}
    frames: list[dict[str, Any]] = []
    cursor = 0
    for row in timeline["rows"]:
        if row["start_ms"] != cursor:
            raise ValueError("Waiting preview phases must be contiguous")
        duration = integer_value(row["duration_ms"], minimum=1, maximum=5000,
                                 context="Waiting preview duration")
        cursor += duration
        source = (source_job / row["after"]).resolve()
        # The reviewed preview also references neutral endpoints in a sibling job.
        if not source.is_relative_to(source_job.parent) or source.suffix != ".png":
            raise ValueError("Waiting preview frame escapes its source archive")
        payload = source.read_bytes()
        digest = sha256_digest(payload)
        if digest not in names:
            image = load_rgba_component(payload)
            if (set(image.getchannel("A").tobytes()) != {0, 255}
                    or planted_foot_bounds(image) != feet):
                raise ValueError("Waiting preview must retain binary alpha and feet")
            name = f"actions/waiting/{len(files):02}-{digest[:16]}.png"
            names[digest] = name
            files[name] = payload
        if frames and frames[-1]["sha256"] == digest:
            # Comparison-only cuts must not interrupt the same displayed sprite.
            frames[-1]["duration_ms"] += duration
        else:
            frames.append(dict(file=names[digest], duration_ms=duration, sha256=digest))
    if cursor != timeline["duration_ms"]:
        raise ValueError("Waiting preview duration does not match its phases")
    manifest = dict(version=1, size=list(HD_FRAME_SIZE),
                    anchor=[96, 194], frames=frames)
    with TemporaryDirectory(prefix="waiting-stage-", dir=asset_root.parent) as folder:
        staging = Path(folder)
        for name, payload in files.items():
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        manifest_path = "actions/waiting.json"
        (staging / manifest_path).write_text(
            json.dumps(manifest, indent=2) + "\n", "utf-8",
        )
        load_hd_waiting_clip(staging)
        pngs = [name for name in files if name != WAITING_REST]
        if any((asset_root / name).is_file()
               and (asset_root / name).read_bytes() != files[name] for name in pngs):
            raise ValueError("Waiting PNG conflicts with an installed image")
        for name in (*pngs, manifest_path):
            prepared = staging / name
            target = asset_root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.is_file() or target.read_bytes() != prepared.read_bytes():
                os.replace(prepared, target)
    return {"playback_frames": len(frames), "new_pngs": len(pngs),
            "duration_ms": cursor}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_job", type=Path)
    parser.add_argument("asset_root", type=Path)
    args = parser.parse_args()
    print(json.dumps(export_waiting(args.source_job, args.asset_root)))


if __name__ == "__main__":
    main()
