"""Avoid reusing failed Pages identities and republishing an already live site."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from scripts.verify_room_deployment import PUBLIC_ROOM_URL


def github(path: str, *, missing: bool = False) -> dict[str, Any] | None:
    result = subprocess.run(
        ["gh", "api", path], capture_output=True, encoding="utf8", check=False
    )
    if result.returncode:
        if missing and "HTTP 404" in result.stderr:
            return None
        raise RuntimeError(f"Cannot check Pages state: {result.stderr.strip()}")
    value: dict[str, Any] = json.loads(result.stdout)
    return value


def already_public(site: Path) -> bool:
    for name in ("install.json", "index.html", "sw.js"):
        request = urllib.request.Request(
            PUBLIC_ROOM_URL + name + f"?preflight={time.time_ns()}",
            headers={"Cache-Control": "no-cache"},
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                if response.read() != (site / name).read_bytes():
                    return False
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return False
            raise RuntimeError(
                f"Public Pages preflight failed: HTTP {error.code}"
            ) from None
        except OSError as error:
            raise RuntimeError(
                f"Public Pages preflight is unreachable: {error}"
            ) from None
    return True


def previously_attempted(repo: str, commit: str) -> bool:
    # Pages also returns {"status": ""} for commits never deployed. Empty status
    # alone cannot distinguish a fresh identity from a timed-out one.
    runs = github(
        f"repos/{repo}/actions/workflows/room-starter.yml/runs"
        f"?head_sha={commit}&per_page=100"
    )
    for run in (runs or {}).get("workflow_runs", []):
        jobs = github(
            f"repos/{repo}/actions/runs/{run['id']}/jobs?filter=all&per_page=100"
        )
        for job in (jobs or {}).get("jobs", []):
            for step in job.get("steps", []):
                if (
                    step["name"] == "Deploy starter"
                    and step["status"] != "pending"
                    and step.get("conclusion") != "skipped"
                ):
                    return True
    return False


def check(site: Path, repo: str, commit: str) -> bool:
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo) or not re.fullmatch(
        r"[a-f0-9]{40}", commit
    ):
        raise ValueError("A repository and full deployment commit SHA are required")
    paths = [path for path in site.rglob("*") if path.is_file()]
    if not paths or any(path.is_symlink() for path in site.rglob("*")):
        raise ValueError("Deployment site must contain regular files without links")
    for name in ("install.json", "index.html", "sw.js"):
        if not (site / name).is_file():
            raise ValueError(f"Reviewed site is missing {name}")
    descriptor = json.loads((site / "install.json").read_text("utf8"))
    runtime = (site / descriptor["package"]).resolve()
    if not runtime.is_relative_to(site) or not runtime.is_file():
        raise ValueError("Reviewed runtime package is missing or outside the site")
    size = sum(path.stat().st_size for path in paths)
    if size > 1024**3:
        raise ValueError("Deployment site exceeds the 1 GiB Pages limit")
    largest = max(paths, key=lambda path: path.stat().st_size)
    print(
        f"Reviewed site: {len(paths)} files, {size} bytes; largest "
        f"{largest.relative_to(site).as_posix()} ({largest.stat().st_size} bytes)"
    )
    config = github(f"repos/{repo}/pages")
    if config is None or config.get("build_type") != "workflow":
        raise RuntimeError("Pages must be enabled with the reviewed workflow source")
    if already_public(site):
        print(
            "Reviewed starter already public; skip deployment, "
            "retain full live verification"
        )
        return False
    previous = github(f"repos/{repo}/pages/deployments/{commit}", missing=True)
    status = (previous or {}).get("status")
    if status or previously_attempted(repo, commit):
        status = status or "empty status after a prior publication attempt"
        raise RuntimeError(
            f"Pages identity {commit} already exists ({status}). "
            "Do not rerun this deployment commit: after a timeout its status can stay "
            "stale. Inspect/cancel the old Pages deployment and use a fresh deployment "
            "commit with the same reviewed release pin. No new runtime build is needed."
        )
    print("Fresh Pages identity; reviewed site requires publication")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "dist-room/published/room",
    )
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--commit", default=os.environ.get("GITHUB_SHA", ""))
    args = parser.parse_args()
    publish = check(args.site.resolve(), args.repo, args.commit)
    output = f"publish={str(publish).lower()}\n"
    print(output.strip())
    if filename := os.environ.get("GITHUB_OUTPUT"):
        with Path(filename).open("a", encoding="utf8") as stream:
            stream.write(output)


if __name__ == "__main__":
    main()
