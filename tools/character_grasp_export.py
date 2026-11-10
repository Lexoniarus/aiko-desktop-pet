"""Export approved V3 grasp PNGs and semantic markers, without generating art."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PIL import Image

from aiko_pet.infrastructure.grasp_assets import load_grasp_clips


def export_grasp(job: Path, root: Path) -> dict[str, Any]:
    data = json.loads((job / "timeline.json").read_text("utf-8"))
    sequences, keys = data["sequences"], data["keys"]
    inspection = sequences["untersuchen"]["frames"]
    clips = {
        "pick_up": sequences["aufheben"]["frames"][:-1],
        "put_down": sequences["hinlegen"]["frames"],
        "hold_item": [dict(keys["G07"], duration_ms=1000,
                           item_anchor=keys["G07"]["palm_midpoint"])],
        "inspect_item": [r for r in inspection if r["phase"] in {
            "Ankommen", "Nach links führen", "Links betrachten", "Seite wechseln",
        }],
        "inspect_hold": [dict(keys["U-right"], duration_ms=1000,
                              item_anchor=keys["U-right"]["palm_midpoint"])],
        "inspect_return": [r for r in inspection if r["phase"] == "Zur Mitte zurück"],
        "throw_item": sequences["vier-gewinnt"]["frames"],
    }
    manifest: dict[str, Any] = {
        "version": 1, "size": [384, 416], "anchor": [96, 194], "clips": {},
    }
    with TemporaryDirectory(prefix="grasp-stage-", dir=root.parent) as folder:
        staging = Path(folder)
        copied: dict[str, str] = {}
        for name, rows in clips.items():
            frames = []
            elapsed = 0
            for row in rows:
                source = (job / row["file"]).resolve()
                if not source.is_relative_to(job.resolve()):
                    raise ValueError("Grasp source escapes job")
                with Image.open(source) as image:
                    if image.size != (384, 416) or image.mode != "RGBA":
                        raise ValueError("Expected reviewed HD RGBA frame")
                    if set(image.getchannel("A").tobytes()) != {0, 255}:
                        raise ValueError("Expected binary alpha")
                relative = f"actions/grasp/{source.stem.lower()}.png"
                digest = hashlib.sha256(source.read_bytes()).hexdigest()
                if relative in copied and copied[relative] != digest:
                    raise ValueError("Conflicting grasp sources")
                if relative not in copied:
                    destination = staging / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, destination)
                    copied[relative] = digest
                events = ({"attach": ["attach_object"], "detach": ["detach_object"],
                           "throw": ["release_object"]}.get(row.get("event"), []))
                if name == "inspect_item":
                    events = (["inspect_comment"] if elapsed == 400 else
                              ["inspect_emote"] if elapsed == 850 else [])
                anchor = row["item_anchor"]
                visible = not row.get("flight", False)
                frames.append({"file": relative, "duration_ms": row["duration_ms"],
                               "sha256": digest, "events": events,
                               "food_anchor": [round(n / 2) for n in anchor]
                               if visible else None})
                elapsed += row["duration_ms"]
            manifest["clips"][name] = {
                "frames": frames, "hold_last": name not in {"put_down", "throw_item"},
            }
        (staging / "actions/grasp.json").write_text(
            json.dumps(manifest, indent=2) + "\n", "utf-8",
        )
        load_grasp_clips(staging)
        for relative in [*copied, "actions/grasp.json"]:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging / relative, target)
    return {"images": len(copied), "clips": list(clips), "generation_calls": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_job", type=Path)
    parser.add_argument("asset_root", type=Path)
    args = parser.parse_args()
    print(json.dumps(export_grasp(args.source_job, args.asset_root)))


if __name__ == "__main__":
    main()
