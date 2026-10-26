"""Install a complete modular question/request gesture in the 2x waiting slots."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageChops, ImageDraw

from tools.character_export_common import (
    HD_FRAME_SIZE,
    load_rgba_component,
    planted_foot_bounds,
    sha256_digest,
)

POSES = ("idle", "A", "B", "C", "C", "B", "A", "idle")
EYES = ("offen", "offen", "offen", "halboffen", "geschlossen",
        "halboffen", "offen", "offen")
STATUS = "composited_v3_question_request_gesture"


def gray_mask(path: Path, expected_sha: str) -> Image.Image:
    if sha256_digest(path.read_bytes()) != expected_sha:
        raise ValueError(f"Reviewed mask digest mismatch: {path.name}")
    with Image.open(path) as image:
        if image.mode != "L" or image.size != HD_FRAME_SIZE:
            raise ValueError("Expected a 384x416 grayscale mask")
        result: Image.Image = image.copy()
        return result


def export_request(package: Path, hd_root: Path) -> list[dict[str, object]]:
    """Preflight all sources/frames before replacing only the complete waiting set."""
    manifest_path = hd_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    inputs = json.loads((package / "manifest.json").read_text("utf-8"))
    for data in (manifest, inputs):
        if data.get("version") != 1 or data.get("size") != list(HD_FRAME_SIZE):
            raise ValueError("Expected the 384x416 character manifest")
    expected = {f"waiting/{index:02}.png" for index in range(8)}
    paths = [record["path"] for record in manifest["frames"]]
    source_paths = [record["path"] for record in inputs["frames"]]
    if (len(paths) != len(set(paths)) or not expected.issubset(paths)
            or len(source_paths) != 8 or set(source_paths) != expected):
        raise ValueError("Expected each of the eight request slots exactly once")
    idle_payload = (hd_root / "idle/00.png").read_bytes()
    if sha256_digest(idle_payload) != inputs["reference_sha256"]:
        raise ValueError("Reviewed request package uses a different Idle reference")
    idle = load_rgba_component(idle_payload)
    target_feet = planted_foot_bounds(idle)
    lower = (0, 324, HD_FRAME_SIZE[0], HD_FRAME_SIZE[1])
    original_lower = idle.crop(lower).tobytes()
    head_mask = gray_mask(package / "head-mask.png", inputs["head_mask_sha256"])
    eye_mask = gray_mask(package / "eye-mask.png", inputs["eye_mask_sha256"])
    eye_bounds = eye_mask.getbbox()
    if (eye_bounds is None or eye_bounds[0] < 130 or eye_bounds[1] < 170
            or eye_bounds[2] > 250 or eye_bounds[3] > 220):
        raise ValueError("Eye mask must stay inside the reviewed face region")
    head_support = head_mask.point([255 if v else 0 for v in range(256)])
    if not head_support.getbbox():
        raise ValueError("Expected a nonempty fixed Idle head mask")
    no_eyes = eye_mask.point([0 if v else 255 for v in range(256)])
    head_protection = ImageChops.multiply(head_support, no_eyes)
    editable_region = eye_mask.point([255 if v else 0 for v in range(256)])
    ImageDraw.Draw(editable_region).rectangle((120, 240, 264, 323), fill=255)
    never_edit = ImageChops.invert(editable_region)
    originals = inputs["originals"]
    if set(originals) != {"A", "B", "C"}:
        raise ValueError("Expected three distinct native arm-pose sources")
    for pose in ("A", "B", "C"):
        source = originals[pose]
        payload = (package / "originale" / f"{pose}.png").read_bytes()
        if sha256_digest(payload) != source["sha256"]:
            raise ValueError(f"Native source digest mismatch: {pose}")
        with Image.open(package / "originale" / f"{pose}.png") as image:
            if min(image.size) < 1000 or list(image.size) != source["size"]:
                raise ValueError("Native sources need at least 1000px on both axes")
            image.load()
    if len({source["sha256"] for source in originals.values()}) != 3:
        raise ValueError("Native arm poses must be three distinct sources")
    prepared: list[tuple[str, bytes, dict[str, object]]] = []
    repeated: dict[tuple[str, str], bytes] = {}
    for source in inputs["frames"]:
        relative = source["path"]
        number = int(Path(relative).stem)
        pose, eyes = source["pose"], source["eyes"]
        if pose != POSES[number] or eyes != EYES[number]:
            raise ValueError(f"Unexpected request gesture phase: {relative}")
        payload = (package / relative).read_bytes()
        if sha256_digest(payload) != source["sha256"]:
            raise ValueError(f"Reviewed request frame digest mismatch: {relative}")
        image = load_rgba_component(payload)
        alpha = image.getchannel("A")
        if set(alpha.tobytes()) != {0, 255}:
            raise ValueError(f"Request frame requires binary alpha: {relative}")
        if image.crop(lower).tobytes() != original_lower:
            raise ValueError(f"Request frame changes Idle's lower body: {relative}")
        if planted_foot_bounds(image) != target_feet:
            raise ValueError(f"Request frame changes Idle's foot anchor: {relative}")
        difference = ImageChops.difference(image, idle)
        if any(ImageChops.multiply(channel, head_protection).getbbox()
               for channel in difference.split()):
            raise ValueError(f"Request frame changes the fixed Idle head: {relative}")
        allowed = gray_mask(package / "masks" / f"{number:02}.png",
                            source["allowed_mask_sha256"])
        # Allowed modifications are restricted to eyes and arm/hand bands.
        bounds = allowed.getbbox()
        if bounds and (bounds[0] < 120 or bounds[1] < 170
                       or bounds[2] > 265 or bounds[3] > 324):
            raise ValueError("Request mask exceeds the reviewed character region")
        if ImageChops.multiply(allowed, never_edit).getbbox():
            raise ValueError("Request mask must contain only eyes and arm/hand regions")
        outside = allowed.point([0 if v else 255 for v in range(256)])
        if any(ImageChops.multiply(channel, outside).getbbox()
               for channel in difference.split()):
            raise ValueError(f"Request frame changes protected pixels: {relative}")
        if pose == "idle" and payload != idle_payload:
            raise ValueError("Request endpoints must be the exact Idle PNG")
        key = (pose, eyes)
        if repeated.setdefault(key, payload) != payload:
            raise ValueError("Repeated motion phases must reuse the reviewed PNG")
        provenance = None if pose == "idle" else originals[pose]
        record: dict[str, object] = {
            "path": relative,
            "source": f"private-v3-question-request/{relative}",
            "source_size": list(HD_FRAME_SIZE), "source_sha256": source["sha256"],
            "status": STATUS, "semantic_name": "question_request_gesture",
            "pose": pose, "eyes": eyes, "pose_provenance": provenance,
            "eye_provenance": inputs["eye_provenance"][eyes],
            "reference_frame": "idle/00.png",
            "reference_sha256": inputs["reference_sha256"],
            "allowed_mask_sha256": source["allowed_mask_sha256"],
            "fixed_head_mask_sha256": inputs["head_mask_sha256"],
            "scale_calibration": "fixed_idle_body_and_head_with_arm_modules",
            "rendered_foot_anchor": [(target_feet[0] + target_feet[2]) / 2,
                                     target_feet[3]],
            "aspect_rescale_ratio": 1.0,
            "sha256": sha256_digest(payload), "bytes": len(payload),
        }
        prepared.append((relative, payload, record))
    replacements = {relative: record for relative, _, record in prepared}
    manifest["frames"] = [replacements.get(record["path"], record)
                          for record in manifest["frames"]]
    with TemporaryDirectory(prefix="request-gesture-", dir=hd_root.parent) as folder:
        staging = Path(folder)
        (staging / "waiting").mkdir()
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
    parser.add_argument("--hd-root", type=Path, required=True)
    args = parser.parse_args()
    records = export_request(args.package, args.hd_root)
    print(json.dumps({"exported": len(records), "frames": records}, indent=2))


if __name__ == "__main__":
    main()
