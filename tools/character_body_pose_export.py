"""Bake reviewed body orientations with existing heads; never generate art."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PIL import Image

from tools.character_export_common import (
    BINARY_ALPHA_TABLE,
    HD_FRAME_SIZE,
    load_rgba_component,
    sha256_digest,
)


def export_body_poses(package: Path, assets: Path) -> dict[str, Any]:
    """Install a small separate HD pack, preserving both legacy atlases."""
    data = json.loads((package / "package.json").read_text("utf-8"))
    sources: list[dict[str, str]] = []

    def source(relative: str) -> Image.Image:
        path = (package / relative).resolve()
        if not path.is_relative_to(package.resolve()):
            raise ValueError("Body package source escapes its directory")
        payload = path.read_bytes()
        image = load_rgba_component(payload)
        sources.append({
            "file": relative,
            "sha256": sha256_digest(payload),
        })
        return image

    prepared: dict[str, Image.Image] = {}
    clips: dict[str, list[str]] = {}
    for side in ("left", "right"):
        body = source(f"body-{side}.png")
        dx, dy = data["head_offsets"][side]
        directions = list(range(9)) if side == "right" else [0, *range(8, 16)]
        look_name = f"body-look-{side}"
        clips[look_name] = []
        for index, direction in enumerate(directions):
            head = source(f"heads/{direction:02}.png")
            frame = Image.new("RGBA", HD_FRAME_SIZE)
            frame.paste(head, (dx, dy))
            frame.alpha_composite(body)
            relative = f"body_poses/{look_name}/{index:02}.png"
            prepared[relative] = frame
            clips[look_name].append(relative)
        turn_name = f"body-turn-{side}"
        clips[turn_name] = ["frames_2x/idle/00.png"]
        for index in range(1, 5):
            relative = f"body_poses/{turn_name}/{index:02}.png"
            prepared[relative] = source(f"turn-{side}/{index:02}.png")
            clips[turn_name].append(relative)
    if not (assets / "frames_2x/idle/00.png").is_file():
        raise FileNotFoundError("Body orientation needs the existing idle HD pose")
    locomotion: dict[str, dict[str, Any]] = {}
    if data.get("locomotion"):
        keys = ("stand", "01", "03", "07", "00", "stand")
        for side, german, heading in (("left", "links", -1), ("right", "rechts", 1)):
            orient = f"body-orient-{side}"
            clips[orient] = ["frames_2x/idle/00.png"]
            for index in range(1, 9):
                relative = f"body_poses/{orient}/{index:02}.png"
                prepared[relative] = source(f"orient-{side}/{index:02}.png")
                clips[orient].append(relative)
            locomotion[orient] = dict(
                kind="turn",
                heading=heading,
                gaze=None,
                durations=[140] * 9,
                family="",
                stride=0,
            )
            axes = range(2, 7) if side == "right" else range(10, 15)
            for axis in ["profil", *(f"{v:02}" for v in axes)]:
                name = f"body-step-{side}-{axis}"
                clips[name] = []
                for key in keys:
                    body = source(f"step-{side}/{key}.png")
                    head = source(f"step-head-{side}/{axis}.png")
                    frame = Image.new("RGBA", HD_FRAME_SIZE)
                    frame.paste(head, (0, {"01": 2, "03": -2}.get(key, 0)))
                    if axis == "profil":
                        frame = Image.alpha_composite(body, frame)
                    else:
                        frame.alpha_composite(body)
                    relative = f"body_poses/{name}/{key}.png"
                    prepared[relative] = frame
                    clips[name].append(relative)
                locomotion[name] = dict(
                    kind="step",
                    heading=heading,
                    gaze=None if axis == "profil" else int(axis),
                    durations=[60, 110, 100, 130, 120, 100],
                    family=f"body-step-{side}",
                    stride=16,
                )
    manifest = {
        "version": 1,
        "size": list(HD_FRAME_SIZE),
        "clips": clips,
        "sources": sources,
    }
    if locomotion:
        manifest.update(version=2, locomotion=locomotion)
    # Finish validation and PNG encoding before replacing any installed file.
    assets.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="body-poses-", dir=assets.parent) as folder:
        staging = Path(folder)
        for relative, frame in prepared.items():
            # Windows color-key rendering requires binary edge alpha.
            frame.putalpha(frame.getchannel("A").point(BINARY_ALPHA_TABLE))
            path = staging / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            frame.save(path)
        manifest_relative = "body_poses/manifest.json"
        (staging / manifest_relative).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            "utf-8",
        )
        for relative in (*prepared, manifest_relative):
            target = assets / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staging / relative, target)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("assets", type=Path)
    args = parser.parse_args()
    export_body_poses(args.package, args.assets)


if __name__ == "__main__":
    main()
