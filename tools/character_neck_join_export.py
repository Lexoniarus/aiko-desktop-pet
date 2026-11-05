"""Install reviewed local neck joins without re-registering any character art."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from PIL import Image

from tools.character_export_common import load_rgba_component, sha256_digest

NECK_BOUNDS = (165, 233, 231, 259)


def expected_paths() -> set[str]:
    """Complete inspected family, including unchanged turn/profile controls."""
    paths = {f"frames_2x/look/{i:02}.png" for i in range(16)}
    paths.update(f"frames_2x/idle/{i:02}.png" for i in range(8))
    for side, axes in (("right", range(2, 7)), ("left", range(10, 15))):
        paths.update(f"body_poses/body-look-{side}/{i:02}.png" for i in range(9))
        for axis in ("profil", *(f"{i:02}" for i in axes)):
            paths.update(f"body_poses/body-step-{side}-{axis}/{key}.png"
                         for key in ("stand", "01", "03", "07", "00"))
        for family, count in (("turn", 4), ("orient", 8)):
            paths.update(f"body_poses/body-{family}-{side}/{i:02}.png"
                         for i in range(1, count + 1))
    return paths


def protected_pixels(image: Image.Image) -> bytes:
    """Stable RGBA fingerprint of everything outside the authorized join."""
    image = image.copy()
    image.paste((0, 0, 0, 0), NECK_BOUNDS)
    return image.tobytes()


def export_neck_joins(package: Path, assets: Path) -> dict[str, Any]:
    """Validate all inspected poses and sources, stage changes, then install.

    The package contains complete reviewed PNGs; no artwork is recomposed
    here. A changed source must live in its private frames folder. Controls,
    pose anchors, timings and non-join pixels are protected before any write.
    """
    inputs = json.loads((package / "vorschau-manifest.json").read_text("utf-8"))
    if inputs.get("do_not_install"):
        raise ValueError("This intermediate neck package was withdrawn")
    rows = inputs["frames"]
    paths = [row["file"] for row in rows]
    if (len(paths) != len(set(paths)) or set(paths) != expected_paths()
            or inputs["reviewed_frames"] != len(paths)
            or inputs.get("image_generation_calls") != 0):
        raise ValueError("Expected the complete reviewed neck-join family")
    hd_path, body_path = (assets / "frames_2x/manifest.json",
                          assets / "body_poses/manifest.json")
    hd: dict[str, Any] = json.loads(hd_path.read_text("utf-8"))
    body: dict[str, Any] = json.loads(body_path.read_text("utf-8"))
    if (hd.get("version") != 1 or body.get("version") != 2
            or hd.get("size") != [384, 416] or body.get("size") != [384, 416]):
        raise ValueError("Expected the existing HD/body-pose manifests")
    frame_records = {r["path"]: r for r in hd["frames"]}
    existing_joins = {r["file"]: r for r in hd.get(
        "neck_join_corrections", {},
    ).get("frames", [])}
    prepared: dict[str, bytes] = {}
    records: dict[str, list[dict[str, Any]]] = {"hd": [], "body": []}
    source_root = (package / "frames").resolve()
    for row in rows:
        relative = row["file"]
        current_payload = (assets / relative).read_bytes()
        current_sha = sha256_digest(current_payload)
        if current_sha not in (row["before_sha256"], row["after_sha256"]):
            raise ValueError(f"Installed pose changed since review: {relative}")
        if row.get("head_translation") != [0, 0] or row.get("head_scale") != 1:
            raise ValueError("Neck corrections cannot transform heads")
        if not row["changed_pixels"]:
            if row["before_sha256"] != row["after_sha256"]:
                raise ValueError("Unchanged control has different digests")
            # A contour revision can keep a previously corrected pose exactly.
            # Retain its provenance instead of dropping it from the final pack.
            if relative in existing_joins:
                info = dict(existing_joins[relative])
                if info["sha256"] != current_sha:
                    raise ValueError("Existing join provenance digest mismatch")
                if inputs.get("neck_owner") == "head":
                    info.update(
                        method="complete_original_neck_silhouette_collar_foreground",
                        bounds_2x=list(NECK_BOUNDS),
                    )
                category = "hd" if relative.startswith("frames_2x/") else "body"
                records[category].append(info)
            continue
        if row["group"] not in ("front", "stand-left", "stand-right",
                                 "walk-left", "walk-right"):
            raise ValueError("Neutral, profile and turning controls must be retained")
        source = Path(row["after"]).resolve()
        if not source.is_relative_to(source_root):
            raise ValueError("Neck source escapes the private frames directory")
        payload = source.read_bytes()
        if sha256_digest(payload) != row["after_sha256"]:
            raise ValueError(f"Reviewed neck source digest mismatch: {relative}")
        current, candidate = (load_rgba_component(current_payload),
                              load_rgba_component(payload))
        if protected_pixels(current) != protected_pixels(candidate):
            raise ValueError(f"Neck correction changes protected art: {relative}")
        if not set(candidate.getchannel("A").tobytes()) <= {0, 255}:
            raise ValueError("Expected binary-alpha reviewed neck image")
        info = {
            "file": relative, "base_sha256": row["before_sha256"],
            "sha256": row["after_sha256"], "bounds_2x": list(NECK_BOUNDS),
            "changed_pixels": row["changed_pixels"],
            "method": ("original_chin_visibility" if row["group"] in (
                "front", "stand-left", "stand-right",
            ) else "original_neck_and_contour_to_phase_collar"),
            "head_translation": [0, 0], "head_scale": 1,
        }
        if inputs.get("neck_owner") == "head":
            info["method"] = "complete_original_neck_silhouette_collar_foreground"
        if row.get("walk_collar_fit"):
            if row["group"] not in ("walk-left", "walk-right"):
                raise ValueError("Step collar fitting is limited to walking poses")
            anchor = row["walk_collar_fit"]["jaw_boundary_y"]
            if not 233 <= anchor <= 247 or current.crop(
                (0, 0, 384, anchor),
            ).tobytes() != candidate.crop((0, 0, 384, anchor)).tobytes():
                raise ValueError("Step collar fitting must retain the approved jaw")
            info.update(method="native_neck_fitted_to_step_collar",
                        walk_collar_fit=row["walk_collar_fit"])
        category = "hd" if relative.startswith("frames_2x/") else "body"
        records[category].append(info)
        if category == "hd":
            record = frame_records[relative.removeprefix("frames_2x/")]
            record.update(sha256=row["after_sha256"], bytes=len(payload),
                          neck_join=info)
        prepared[relative] = payload
    if len(prepared) != inputs["changed_preview_frames"]:
        raise ValueError("Reviewed neck correction count mismatch")
    # Keep the strict body-pose manifest byte-identical. Provenance for both
    # packs belongs to this HD metadata extension, not new runtime clip fields.
    hd["neck_join_corrections"] = {
        "version": 1, "bounds_2x": list(NECK_BOUNDS),
        "source_kind": "reviewed_existing_source_pixels_no_generation",
        "frames": sorted([*records["hd"], *records["body"]], key=lambda r: r["file"]),
    }
    if inputs.get("neck_owner") == "head":
        hd["neck_join_corrections"]["neck_owner"] = "head"
    prepared["frames_2x/manifest.json"] = (
        json.dumps(hd, ensure_ascii=False, indent=2) + "\n"
    ).encode("utf-8")
    # Every source, control and protected pixel is checked before replacement.
    with TemporaryDirectory(prefix="neck-join-", dir=assets.parent) as folder:
        staging = Path(folder)
        for relative, payload in prepared.items():
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        for relative, payload in prepared.items():
            target = assets / relative
            if target.read_bytes() != payload:
                os.replace(staging / relative, target)
    return {"corrected_frames": len(prepared) - 1,
            "hd_frames": len(records["hd"]), "body_frames": len(records["body"])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package", type=Path)
    parser.add_argument("assets", type=Path)
    args = parser.parse_args()
    print(json.dumps(export_neck_joins(args.package, args.assets)))


if __name__ == "__main__":
    main()
