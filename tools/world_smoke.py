"""Start a disposable World test session; never seed the normal user's save."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from aiko_pet.application.settings import PetSettings
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore, default_save_path
from aiko_pet.pet.state import PetState

SCENARIOS = {"hungry": (55, 55), "curious": (76, 60), "full": (100, 100)}


def prepare_session(path: Path, *, scenario: str) -> StateStore:
    """Explicit restart paths reuse existing data instead of silently resetting."""
    if path.resolve() == default_save_path().resolve():
        raise ValueError("The smoke test must not use the normal save path")
    store = StateStore(path)
    if not path.exists():
        satiety, energy = SCENARIOS[scenario]
        store.save(
            PetState(satiety=satiety, energy=energy),
            PetSettings(auto_walk=False, auto_routine=False, observe_computer=False,
                        learn_rhythm=False, spontaneous_talk=False),
        )
    return store


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=tuple(SCENARIOS), default="hungry")
    parser.add_argument("--save-path", type=Path)
    parser.add_argument("--auto-close-ms", type=int, default=0, help=argparse.SUPPRESS)
    args = parser.parse_args()
    path = args.save_path or (
        Path(tempfile.mkdtemp(prefix="aiko-world-smoke-")) / "state.json"
    )
    print(f"Isolated World test save: {path}", flush=True)
    print(f'Restart: python -m tools.world_smoke --save-path "{path}"', flush=True)
    app = DesktopPet(store=prepare_session(path, scenario=args.scenario))
    if args.auto_close_ms > 0:
        app.root.after(args.auto_close_ms, app.quit)
    app.run()


if __name__ == "__main__":
    main()
