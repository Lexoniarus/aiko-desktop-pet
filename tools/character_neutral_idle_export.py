"""Install approved neutral Idle phases without touching any gaze or body pose."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from tools.character_export_common import (
    HD_FRAME_SIZE,
    load_rgba_component,
    sha256_digest,
)
from tools.character_idle_modular_export import PHASES


def export_neutral_idle(assets: Path) -> dict[str, Any]:
    """Validate all eight approved neutral PNGs, then replace Idle slots only.

    The expressions pack owns the approved complete neutral artwork. No head
    or body component is reassembled here. Non-Idle frame records, all gaze
    images and the separate body-pose pack are outside this export's scope.
    """
    hd = assets / "frames_2x"
    manifest: dict[str, Any] = json.loads(
        (hd / "manifest.json").read_text("utf-8"),
    )
    expressions = json.loads((assets / "expressions/manifest.json").read_text("utf-8"))
    for data in (manifest, expressions):
        if data.get("version") != 1 or data.get("size") != list(HD_FRAME_SIZE):
            raise ValueError("Expected the reviewed HD manifest")
    if "frontal_reference" in manifest:
        raise ValueError("Restore approved gaze/body poses before Idle-only export")
    wanted = {f"idle/{i:02}.png" for i in range(8)}
    paths = [record["path"] for record in manifest["frames"]]
    if len(paths) != len(set(paths)) or not wanted.issubset(paths):
        raise ValueError("Expected each of the eight Idle slots exactly once")
    neutral = expressions["clips"]["rest-neutral"]["frames"]
    if len(neutral) != 8:
        raise ValueError("Expected eight approved neutral phases")
    payloads = []
    for i, record in enumerate(neutral):
        relative = f"expressions/rest-neutral/{i:02}.png"
        if record["file"] != relative:
            raise ValueError("Unexpected neutral phase path")
        payload = (assets / relative).read_bytes()
        if sha256_digest(payload) != record["sha256"]:
            raise ValueError("Neutral phase digest mismatch")
        load_rgba_component(payload)
        payloads.append(payload)
    replacements = {
        f"idle/{i:02}.png": {
            "path": f"idle/{i:02}.png",
            "source": f"expressions/rest-neutral/{i:02}.png",
            "source_sha256": sha256_digest(payload),
            "source_size": list(HD_FRAME_SIZE),
            "status": "approved_neutral_idle_only",
            "eye_phase": PHASES[i],
            "sha256": sha256_digest(payload),
            "bytes": len(payload),
        } for i, payload in enumerate(payloads)
    }
    manifest["frames"] = [replacements.get(record["path"], record)
                          for record in manifest["frames"]]
    manifest["neutral_idle_reference"] = {
        "file": "expressions/rest-neutral/00.png",
        "sha256": sha256_digest(payloads[0]),
        "scope": "eight_idle_slots_only_gaze_and_body_poses_unchanged",
    }
    # Finish every input check and staging write before replacing runtime files.
    with TemporaryDirectory(prefix="neutral-idle-", dir=assets.parent) as temporary:
        staging = Path(temporary)
        (staging / "idle").mkdir()
        for i, payload in enumerate(payloads):
            (staging / f"idle/{i:02}.png").write_bytes(payload)
        (staging / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", "utf-8",
        )
        for relative in (*replacements, "manifest.json"):
            source, target = staging / relative, hd / relative
            if source.read_bytes() != target.read_bytes():
                os.replace(source, target)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assets", type=Path)
    args = parser.parse_args()
    export_neutral_idle(args.assets)
    print("Exported eight approved neutral Idle phases; other poses unchanged.")


if __name__ == "__main__":
    main()
