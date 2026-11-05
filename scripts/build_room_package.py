"""Build a private offline runtime ZIP from pinned dependencies and source IDs.

Never reads personal saves. The supplied reference stays outside the repository;
only the approved room images used by v16 enter the generated distribution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aiko_pet.asset_paths import ASSET_ROOT  # noqa: E402
from aiko_pet.infrastructure.character_assets import load_character_catalog  # noqa: E402
from aiko_pet.infrastructure.item_assets import load_item_catalog  # noqa: E402
from aiko_pet.infrastructure.sqlite.schema import SCHEMA_VERSION  # noqa: E402

ROOM_IMAGES = {
    "kitchen": "anime-architecture-empty-v4.png",
    "living": "anime-living-v2.png",
    "door": "entry-door-chibi-v2.png",
    "kitchenUnit": "kitchen-unit-chibi-v2.png",
    "fridge": "fridge-chibi-v3.png",
    "bed": "bed-single-chibi-v1.png",
    "desk": "desk-chibi-v1.png",
    "shelf": "wall-shelf-chibi-v1.png",
    "table": "coffee-table-chibi-v1.png",
    "plant": "plant-chibi-v1.png",
}


def encoded(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf8")


def archive(path: Path, files: dict[str, bytes]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(path, "w", compression=ZIP_DEFLATED, compresslevel=6) as output:
        for name, contents in files.items():
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            output.writestr(info, contents)


def download(url: str, target: Path, digest: str) -> bytes:
    if target.is_file():
        content = target.read_bytes()
        if hashlib.sha256(content).hexdigest() == digest:
            return content
    request = urllib.request.Request(url, headers={"User-Agent": "AikoRoomBuilder/1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        content = response.read(40 * 1024 * 1024)
    if hashlib.sha256(content).hexdigest() != digest:
        raise ValueError(f"Dependency digest mismatch: {target.name}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return content


def python_wheel(project: str, version: str, cache: Path) -> tuple[str, bytes]:
    with urllib.request.urlopen(f"https://pypi.org/pypi/{project}/{version}/json", timeout=30) as response:
        metadata = json.load(response)
    wheel = next(item for item in metadata["urls"]
                 if item["filename"].endswith("-py3-none-any.whl"))
    return wheel["filename"], download(wheel["url"], cache / wheel["filename"],
                                       wheel["digests"]["sha256"])


def runtime_assets() -> dict[str, Any]:
    catalog = load_character_catalog()
    clips = {}
    for name in set(catalog.clips) | set(catalog.body_clips) | set(catalog.expression_clips):
        clip = catalog.clip_for(name, 2)
        frames = []
        for frame in clip.frames:
            file = frame.file
            relative = file.relative_to(ASSET_ROOT)
            if relative.parts[0] == "frames":
                hd = ASSET_ROOT / "frames_2x" / Path(*relative.parts[1:])
                if hd.is_file():
                    file = hd
            frames.append({
                "file": "assets/" + file.relative_to(ASSET_ROOT).as_posix(),
                "duration": frame.duration_ms, "foodAnchor": frame.food_anchor,
                "foreground": ("assets/" + frame.hand_foreground.relative_to(ASSET_ROOT).as_posix())
                if frame.hand_foreground else None,
            })
        clips[name] = dict(frames=frames, order=list(clip.playback_order),
                           loop=clip.loop, anchor=clip.anchor,
                           duration=clip.duration_seconds)
    items = load_item_catalog()
    item_files = {key: {"file": "assets/" + item.sprites[2].render_path.relative_to(ASSET_ROOT).as_posix(),
                         "label": item.label}
                  for key, item in items.foods.items()}
    for key, item in items.readables.items():
        item_files[key] = {"file": "assets/" + item.sprites[2].render_path.relative_to(ASSET_ROOT).as_posix(),
                           "label": item.label}
    return {"clips": clips, "items": item_files, "room": ROOM_IMAGES}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prototype", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "dist-room")
    args = parser.parse_args()
    web, output = ROOT / "web", args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    cache = web / ".runtime"
    package = json.loads((web / "package.json").read_text("utf8"))
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    version = f"{package['version']}-{sha[:12]}"
    files = {"app/" + path.relative_to(web / "dist-runtime").as_posix(): path.read_bytes()
             for path in sorted((web / "dist-runtime").rglob("*")) if path.is_file()}
    if "app/app.js" not in files:
        raise ValueError("Build the web runtime first")
    runtime = web / "node_modules/pyodide"
    for name in ("pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm",
                 "python_stdlib.zip", "pyodide-lock.json", "package.json"):
        files["runtime/" + name] = (runtime / name).read_bytes()
    lock = json.loads((runtime / "pyodide-lock.json").read_text("utf8"))
    pending = ["sqlite3"] if "sqlite3" in lock["packages"] else []
    fetched = set()
    while pending:
        name = pending.pop()
        if name in fetched:
            continue
        fetched.add(name)
        record = lock["packages"][name]
        pending.extend(record["depends"])
        filename = record["file_name"]
        url = f"https://cdn.jsdelivr.net/pyodide/v{package['dependencies']['pyodide']}/full/{filename}"
        files["runtime/" + filename] = download(url, cache / filename, record["sha256"])
    wheels = []
    for name, pinned in (("astronomy-engine", "2.1.19"), ("pyjokes", "0.8.3")):
        filename, contents = python_wheel(name, pinned, cache)
        files["python/" + filename] = contents
        wheels.append(filename)
    files["python/wheels.json"] = encoded(wheels)
    # Keep packaged sources/resources canonical. No database, local log, font,
    # authoring originals or bytecode is selected from the checkout.
    python_files = {}
    for path in sorted((ROOT / "aiko_pet").rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(ROOT)
        if path.suffix == ".py" or "data" in relative.parts:
            python_files[relative.as_posix()] = path.read_bytes()
        elif "assets" in relative.parts and path.suffix in (".png", ".json"):
            python_files[relative.as_posix()] = path.read_bytes()
        if "assets" in relative.parts and path.suffix == ".png":
            files["assets/" + path.relative_to(ASSET_ROOT).as_posix()] = path.read_bytes()
    code_archive = cache / "aiko.zip"
    archive(code_archive, python_files)
    files["python/aiko.zip"] = code_archive.read_bytes()
    files["runtime-assets.json"] = encoded(runtime_assets())
    with ZipFile(args.prototype) as reference:
        for filename in ROOM_IMAGES.values():
            files["room/" + filename] = reference.read("aiko-360-prototype/assets/" + filename)
    for path in sorted((ROOT / "LICENSES").glob("*.txt")):
        files["licenses/" + path.name] = path.read_bytes()
    files["licenses/ASSETS.md"] = (ROOT / "ASSETS.md").read_bytes()
    manifest = dict(
        format=1, protocol=1, saveSchema=SCHEMA_VERSION, version=version, entry="app/app.js",
        sourceCommit=sha, pyodide=package["dependencies"]["pyodide"],
        prototypeSHA256=hashlib.sha256(args.prototype.read_bytes()).hexdigest(),
        files={name: dict(size=len(content), sha256=hashlib.sha256(content).hexdigest())
               for name, content in sorted(files.items())},
    )
    zip_path = output / f"aiko-room-{version}.zip"
    archive(zip_path, {"manifest.json": encoded(manifest), **dict(sorted(files.items()))})
    starter = output / "starter"
    shutil.copytree(web / "dist-starter", starter, dirs_exist_ok=True)
    (output / "BUILD.json").write_bytes(encoded(dict(
        version=version, sourceCommit=sha, package=zip_path.name,
        sha256=hashlib.sha256(zip_path.read_bytes()).hexdigest(),
        device="iPad 9th generation, iPadOS 26.6; device verification pending",
    )))
    print(f"Built {zip_path.name}: {zip_path.stat().st_size / 1024 / 1024:.1f} MiB")


if __name__ == "__main__":
    main()
