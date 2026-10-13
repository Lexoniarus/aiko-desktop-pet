"""Prepare the approved full-width desktop export; Pillow is build-time only."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from PIL import Image

from aiko_pet.presentation.animation_timing import load_timing_policy

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets/aiko-anime-8-frames/aiko-anime-compact/animations-8"
DESTINATION = ROOT / "aiko_pet/assets"
ALPHA_THRESHOLD = [255 if alpha >= 128 else 0 for alpha in range(256)]


def prepare(source: Path = SOURCE, destination: Path = DESTINATION) -> None:
    """Replace only the character frame tree, retaining untouched source art."""
    catalog = json.loads((source / "catalog.json").read_text(encoding="utf-8"))
    policy = load_timing_policy(destination)
    frame_root = (destination / "frames").resolve()
    if not frame_root.is_relative_to(destination.resolve()):
        raise ValueError("Invalid runtime frame destination")
    frame_root.mkdir(parents=True, exist_ok=True)
    animations: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    hashes: dict[str, str] = {}
    expected: set[Path] = set()

    def copy_frame(original: Path, relative: Path) -> int:
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(original) as raw:
            image = raw.convert("RGBA")
        if image.size != (192, 208):
            raise ValueError(f"Unexpected source dimensions: {original}")
        image.putalpha(image.getchannel("A").point(ALPHA_THRESHOLD))
        bounds = image.getbbox()
        if bounds is None:
            raise ValueError(f"Empty character image: {original}")
        image.save(path, optimize=True)
        hashes[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        expected.add(path.resolve())
        return int(bounds[3])

    for item in catalog["animations"]:
        # The desktop uses directional walking; the generic clip has no caller.
        if item["state"] == "running":
            continue
        original = source / item["manifest"]
        entry = json.loads(original.read_text(encoding="utf-8"))
        state = entry["state"]
        if len(entry["frames"]) != policy.regular_frames:
            raise ValueError(f"Expected eight animation frames: {state}")
        entry["source_anchor"] = entry["anchor"]
        ground = 0
        for index, frame in enumerate(entry["frames"]):
            frame["source_duration_ms"] = frame["duration_ms"]
            # A clip's own eight holds are equal, independently of its peers.
            frame["duration_ms"] = policy.duration_for(state)
            relative = Path("frames") / state / f"{index:02d}.png"
            ground = max(ground, copy_frame(
                original.parent / frame["file"], relative,
            ))
            frame["file"] = relative.as_posix()
            if "hand_foreground" in frame:
                relative_hand = Path("hand-foreground") / state / f"{index:02d}.png"
                copy_frame(original.parent / frame["hand_foreground"], relative_hand)
                frame["hand_foreground"] = relative_hand.as_posix()
        entry["anchor"] = [192 // 2, ground]
        animations.append(entry)
        counts[state] = len(entry["frames"])
    directions = json.loads(
        (source / "look-directions/directions.json").read_text(encoding="utf-8"),
    )
    gaze_frames: list[dict[str, Any]] = []
    ground = 0
    for index, frame in enumerate(directions["directions"]):
        relative = Path("frames/look") / f"{index:02d}.png"
        ground = max(ground, copy_frame(
            source / "look-directions" / frame["file"], relative,
        ))
        gaze_frames.append({
            "file": relative.as_posix(), "duration_ms": 1000,
            "degrees_clockwise_from_up": frame["degrees_clockwise_from_up"],
        })
    if len(gaze_frames) != policy.gaze_directions:
        raise ValueError("Expected sixteen gaze poses")
    animations.append({
        "state": "look", "loop": True, "anchor": [96, ground],
        "frames": gaze_frames, "return_to": "idle",
    })
    counts["look"] = len(gaze_frames)
    # Old poses with higher frame numbers must not survive a replacement.
    for old in frame_root.rglob("*.png"):
        if old.resolve() not in expected:
            old.unlink()
    runtime = {"version": 1, "frame_size": [192, 208], "animations": animations}
    provenance = {
        "source_asset": "Aiko_Anime_8_Frames_Komplett.zip / animations-8",
        "source_catalog_sha256": hashlib.sha256(
            (source / "catalog.json").read_bytes(),
        ).hexdigest(),
        "frame_counts": counts, "size": [192, 208], "alpha_threshold": 128,
        "license": "../../assets/aiko-anime-8-frames/LICENSE.md",
        "preparation": "Full-width copies; binary alpha; visible ground anchors",
        "timing_profile": (
            "Even frame holds within each eight-frame clip; "
            "activity-specific tempos; ambient blink gaps are separate; "
            "16 static gaze poses; original times retained"
        ),
        "runtime_sha256": hashes,
    }
    for name, data in (("animations.json", runtime), ("provenance.json", provenance)):
        (destination / name).write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8", newline="\n",
        )
    shutil.copyfile(
        ROOT / "assets/aiko-anime-8-frames/LICENSE.md",
        destination / "AIKO_ANIME_ASSET_TERMS.md",
    )
    print(f"Prepared {sum(counts.values())} poses at 192x208; source art unchanged")


if __name__ == "__main__":
    prepare()
