"""Install reviewed eye-only Idle composites without changing runtime timing."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image, ImageChops

from tools.character_export_common import (
    HD_FRAME_SIZE,
    load_rgba_component,
    sha256_digest,
)

PHASES = ("offen", "offen", "halboffen", "geschlossen", "halboffen",
          "offen", "offen", "offen")
STATUS = "composited_v3_idle_fixed_head_eyes_only"


def export_modular_idle(package: Path, hd_root: Path) -> list[dict[str, object]]:
    """Validate the entire package before replacing eight Idle PNGs/records."""
    manifest_path = hd_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    inputs = json.loads((package / "manifest.json").read_text("utf-8"))
    for data in (manifest, inputs):
        if data.get("version") != 1 or data.get("size") != list(HD_FRAME_SIZE):
            raise ValueError("Expected the 384x416 character manifest")
    expected = {f"idle/{index:02}.png" for index in range(8)}
    paths = [record["path"] for record in manifest["frames"]]
    source_paths = [record["path"] for record in inputs["frames"]]
    if (len(paths) != len(set(paths)) or not expected.issubset(paths)
            or len(source_paths) != 8 or set(source_paths) != expected):
        raise ValueError("Expected each of the eight Idle slots exactly once")
    reference_payload = (hd_root / "idle/00.png").read_bytes()
    if sha256_digest(reference_payload) != inputs["reference_sha256"]:
        raise ValueError("Reviewed package uses a different Idle reference")
    reference = load_rgba_component(reference_payload)
    components = {}
    for name in ("body", "head"):
        payload = (package / f"{name}.png").read_bytes()
        if sha256_digest(payload) != inputs[f"{name}_sha256"]:
            raise ValueError(f"Reviewed {name} digest mismatch")
        components[name] = load_rgba_component(payload)
    restored = Image.alpha_composite(components["head"], components["body"])
    if restored.convert("RGBa").tobytes() != reference.convert("RGBa").tobytes():
        raise ValueError("Reviewed head/body must reassemble the exact Idle")
    mask_payload = (package / "eye-mask.png").read_bytes()
    if sha256_digest(mask_payload) != inputs["eye_mask_sha256"]:
        raise ValueError("Reviewed eye mask digest mismatch")
    with Image.open(package / "eye-mask.png") as source_mask:
        if source_mask.mode != "L" or source_mask.size != HD_FRAME_SIZE:
            raise ValueError("Expected a 384x416 grayscale eye mask")
        mask = source_mask.copy()
    bounds = mask.getbbox()
    if (bounds is None or bounds[0] < 130 or bounds[1] < 170
            or bounds[2] > 250 or bounds[3] > 220):
        raise ValueError("Eye mask must stay inside the reviewed eye region")
    protected = mask.point([255 if value == 0 else 0 for value in range(256)])
    reference_alpha = reference.getchannel("A").tobytes()
    prepared: list[tuple[str, bytes, dict[str, object]]] = []
    phase_digests: dict[str, str] = {}
    for source in inputs["frames"]:
        relative = source["path"]
        number = int(Path(relative).stem)
        phase = source["phase"]
        if phase != PHASES[number]:
            raise ValueError(f"Unexpected blink phase in Idle slot: {relative}")
        payload = (package / relative).read_bytes()
        eye_payload = (package / "eyes" / f"{phase}.png").read_bytes()
        if (sha256_digest(payload) != source["sha256"]
                or sha256_digest(eye_payload) != source["eye_sha256"]):
            raise ValueError(f"Reviewed frame or eye digest mismatch: {relative}")
        load_rgba_component(eye_payload)
        image = load_rgba_component(payload)
        if image.getchannel("A").tobytes() != reference_alpha:
            raise ValueError(f"Idle frame changes the reference silhouette: {relative}")
        difference = ImageChops.difference(image, reference)
        if any(ImageChops.multiply(channel, protected).getbbox()
               for channel in difference.split()):
            raise ValueError(f"Idle frame changes pixels outside the eyes: {relative}")
        if phase == "offen" and payload != reference_payload:
            raise ValueError("Open Idle slots must preserve the exact reference PNG")
        previous = phase_digests.setdefault(phase, source["sha256"])
        if previous != source["sha256"]:
            raise ValueError("Repeated eye phases must use the same reviewed pixels")
        record: dict[str, object] = {
            "path": relative,
            "source": f"private-v3-idle-modular/{relative}",
            "source_sha256": source["sha256"],
            "source_size": list(HD_FRAME_SIZE),
            "status": STATUS,
            "source_kind": "reviewed_existing_2x_eye_composite",
            "reference_frame": "idle/00.png",
            "reference_sha256": inputs["reference_sha256"],
            "body_sha256": inputs["body_sha256"],
            "head_sha256": inputs["head_sha256"],
            "eye_mask_sha256": inputs["eye_mask_sha256"],
            "eye_phase": phase,
            "eye_sha256": source["eye_sha256"],
            "eye_provenance": source["eye_provenance"],
            "aspect_rescale_ratio": 1.0,
            "sha256": sha256_digest(payload),
            "bytes": len(payload),
        }
        prepared.append((relative, payload, record))
    replacements = {relative: record for relative, _, record in prepared}
    manifest["frames"] = [replacements.get(record["path"], record)
                          for record in manifest["frames"]]
    with TemporaryDirectory(prefix="idle-modular-", dir=hd_root.parent) as folder:
        staging = Path(folder)
        (staging / "idle").mkdir()
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
    records = export_modular_idle(args.package, args.hd_root)
    print(json.dumps({"exported": len(records), "frames": records}, indent=2))


if __name__ == "__main__":
    main()
