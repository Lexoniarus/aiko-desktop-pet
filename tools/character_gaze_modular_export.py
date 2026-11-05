"""Install reviewed modular gaze frames without changing their registration."""

from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from tools.character_export_common import (
    BINARY_ALPHA_TABLE,
    HD_FRAME_SIZE,
    load_rgba_component,
    planted_foot_bounds,
    sha256_digest,
)

SHARED_BODY_FROM_Y = 260
STATUS = "composited_v3_gaze_shared_idle_body"


def export_modular_gaze(package: Path, hd_root: Path) -> list[dict[str, object]]:
    """Validate every input before staging only the sixteen gaze replacements."""
    manifest_path = hd_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    inputs = json.loads((package / "manifest.json").read_text("utf-8"))
    for data in (manifest, inputs):
        if data.get("version") != 1 or data.get("size") != list(HD_FRAME_SIZE):
            raise ValueError("Expected the 384x416 character manifest")
    expected = {f"look/{index:02}.png" for index in range(16)}
    paths = [record["path"] for record in manifest["frames"]]
    input_paths = [record["path"] for record in inputs["frames"]]
    if (len(paths) != len(set(paths)) or not expected.issubset(paths)
            or len(input_paths) != 16 or set(input_paths) != expected):
        raise ValueError("Expected each of the sixteen gaze sectors exactly once")
    idle_payload = (hd_root / "idle/00.png").read_bytes()
    reference_sha = sha256_digest(idle_payload)
    if inputs["reference_sha256"] != reference_sha:
        raise ValueError("Reviewed package uses a different Idle reference")
    idle = load_rgba_component(idle_payload)
    body_payload = (package / "body.png").read_bytes()
    if sha256_digest(body_payload) != inputs["body_sha256"]:
        raise ValueError("Shared body digest mismatch")
    lower = (0, SHARED_BODY_FROM_Y, HD_FRAME_SIZE[0], HD_FRAME_SIZE[1])
    lower_pixels = idle.crop(lower).tobytes()
    if (inputs.get("shared_body_from_y") != SHARED_BODY_FROM_Y
            or load_rgba_component(body_payload).crop(lower).convert("RGBa").tobytes()
            != idle.crop(lower).convert("RGBa").tobytes()):
        raise ValueError("Shared body must preserve Idle's lower-body pixels")
    target_feet = planted_foot_bounds(idle)
    target_x = (target_feet[0] + target_feet[2]) / 2
    prepared: list[tuple[str, bytes, dict[str, object]]] = []
    for source in inputs["frames"]:
        relative = source["path"]
        payload = (package / relative).read_bytes()
        head_payload = (package / "heads" / Path(relative).name).read_bytes()
        if (sha256_digest(payload) != source["sha256"]
                or sha256_digest(head_payload) != source["head_sha256"]):
            raise ValueError(f"Reviewed frame or head digest mismatch: {relative}")
        load_rgba_component(head_payload)
        image = load_rgba_component(payload)
        if image.crop(lower).tobytes() != lower_pixels:
            raise ValueError(f"Gaze frame changes the shared lower body: {relative}")
        feet = planted_foot_bounds(image)
        actual_x = (feet[0] + feet[2]) / 2
        if feet[3] != target_feet[3] or actual_x != target_x:
            raise ValueError(f"Gaze frame changes Idle's foot anchor: {relative}")
        alpha = image.getchannel("A")
        if alpha.getextrema() != (0, 255):
            raise ValueError(f"Expected transparent and opaque pixels: {relative}")
        normalized = sum(0 < value < 255 for value in alpha.tobytes())
        output_payload = payload
        if normalized:
            image.putalpha(alpha.point(BINARY_ALPHA_TABLE))
            buffer = io.BytesIO()
            image.save(buffer, format="PNG", optimize=True)
            output_payload = buffer.getvalue()
        number = int(Path(relative).stem)
        record: dict[str, object] = {
            "path": relative,
            "source": f"private-v3-gaze-modular/{relative}",
            "source_sha256": source["sha256"],
            "source_size": list(HD_FRAME_SIZE),
            "status": STATUS,
            "degrees_clockwise_from_up": number * 22.5,
            "reference_frame": "idle/00.png",
            "reference_sha256": reference_sha,
            "scale_calibration": "shared_idle_body_pixels",
            "shared_body_from_y": SHARED_BODY_FROM_Y,
            "body_source": "private-v3-gaze-modular/body.png",
            "body_sha256": inputs["body_sha256"],
            "head_sha256": source["head_sha256"],
            "head_provenance": source["head_provenance"],
            "reference_foot_bounds": list(target_feet),
            "rendered_foot_anchor": [actual_x, feet[3]],
            "foot_anchor_error": [0.0, 0],
            "aspect_rescale_ratio": 1.0,
            "alpha128_normalized_pixels": normalized,
            "sha256": sha256_digest(output_payload),
            "bytes": len(output_payload),
        }
        prepared.append((relative, output_payload, record))
    replacements = {relative: record for relative, _, record in prepared}
    manifest["frames"] = [replacements.get(record["path"], record)
                          for record in manifest["frames"]]
    with TemporaryDirectory(prefix="gaze-modular-", dir=hd_root.parent) as folder:
        staging = Path(folder)
        (staging / "look").mkdir()
        for relative, payload, _ in prepared:
            (staging / relative).write_bytes(payload)
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", "utf-8",
        )
        for relative, _, _ in prepared:
            os.replace(staging / relative, hd_root / relative)
        os.replace(staging / "manifest.json", manifest_path)
    return list(replacements.values())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("--hd-root", required=True, type=Path)
    args = parser.parse_args()
    records = export_modular_gaze(args.package, args.hd_root)
    print(json.dumps({"exported": len(records), "frames": records}, indent=2))


if __name__ == "__main__":
    main()
