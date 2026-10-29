"""Export approved V3 poses with binary alpha for Tk's Windows color key."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import struct
from pathlib import Path

from PIL import Image

SOURCE_IDS = (
    "00-idle-neu", "01-positiv-zugewandt", "02-aufmerksam-nachdenklich",
    "03-unsicher-besorgt", "04-bedrueckt-enttaeuscht", "05-genervt-bestimmt",
)
TARGET_IDS = (
    "rest-neutral", "expression-positive", "expression-questioning",
    "expression-worried", "expression-downcast", "expression-firm",
)


def export(source: Path, asset_root: Path) -> None:
    """Validate the complete job before writing any runtime file."""
    manifest = json.loads((source / "manifest.json").read_text("utf-8"))
    if manifest.get("status") != "USER_VISUALLY_APPROVED_PREVIEW_COMPLETE":
        raise ValueError("A visually approved preview is required")
    entries = {clip["id"]: clip for clip in manifest["clips"]}
    copies: list[tuple[bytes, Path]] = []
    clips: dict[str, object] = {}
    for source_id, target_id in zip(SOURCE_IDS, TARGET_IDS, strict=True):
        frames = entries[source_id]["frames"]
        if len(frames) != 8:
            raise ValueError("Eight approved phases are required")
        records = []
        for index, frame in enumerate(frames):
            original = (source / frame["file"]).resolve()
            if not original.is_relative_to(source.resolve()):
                raise ValueError("Unsafe source path")
            content = original.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            if (digest != frame["sha256"] or content[:8] != b"\x89PNG\r\n\x1a\n"
                    or struct.unpack(">II", content[16:24]) != (384, 416)):
                raise ValueError("Source hash or PNG dimensions changed")
            duration = frame["duration_ms"]
            if type(duration) is not int or not 0 < duration <= 10000:
                raise ValueError("Invalid source timing")
            relative = f"expressions/{target_id}/{index:02}.png"
            # Windows -transparentcolor removes exact magenta, not magenta
            # blended under a fractional alpha. Preserve every RGB pixel and
            # threshold alpha only; private approved originals remain intact.
            with Image.open(io.BytesIO(content)) as image:
                exported = image.convert("RGBA")
                alpha = exported.getchannel("A").point([0] * 128 + [255] * 128)
                exported.putalpha(alpha)
                encoded = io.BytesIO()
                exported.save(encoded, format="PNG")
                normalized = encoded.getvalue()
            copies.append((normalized, asset_root / relative))
            records.append(dict(file=relative, duration_ms=duration,
                                sha256=hashlib.sha256(normalized).hexdigest(),
                                source_sha256=digest))
        clips[target_id] = dict(anchor=[96, 194], frames=records)
    for content, target in copies:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    destination = asset_root / "expressions" / "manifest.json"
    destination.write_text(json.dumps(dict(version=1, size=[384, 416], clips=clips),
                                      indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("asset_root", type=Path)
    arguments = parser.parse_args()
    export(arguments.source, arguments.asset_root)
