"""Start a disposable World test session; never seed the normal user's save."""

from __future__ import annotations

import argparse
import tempfile
import time
from pathlib import Path

from aiko_pet.application.settings import PetSettings
from aiko_pet.application.social_history import SocialContentHistory
from aiko_pet.application.storage_contracts import SaveRevision
from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore, default_save_path
from aiko_pet.infrastructure.save_paths import resolve_save_paths
from aiko_pet.pet.mind.adaptive_models import AdaptiveMemory
from aiko_pet.pet.state import PetState
from aiko_pet.world.contracts import ObjectFootprint
from aiko_pet.world.state import WorldState
from tools.pet_test_support import set_test_pet_values

SCENARIOS = {"hungry": (55, 55), "curious": (76, 60), "full": (100, 100)}


def seed_stock(world: WorldState, *, x: float, footprint: ObjectFootprint,
               count: int) -> None:
    """Fresh isolated arrangements use actual runtime geometry, no fake memory."""
    if world.snapshot().objects or count not in (1, 2):
        raise ValueError("Stock arrangements require an empty test World and 1-2 items")
    surface = world.snapshot().surface
    spacing = 3 * (footprint.left + footprint.right)
    for index in range(count):
        world.place_resting("onigiri", surface.ground_x(x + index * spacing, footprint),
                            footprint)


def prepare_session(
    path: Path, *, scenario: str, needs: str | None = None,
) -> StateStore:
    """Explicit restart paths reuse existing data instead of silently resetting."""
    selected = resolve_save_paths(path)
    normal = resolve_save_paths(default_save_path())
    if ({selected.database.resolve(), selected.legacy_json.resolve()}
            & {normal.database.resolve(), normal.legacy_json.resolve()}):
        raise ValueError("The smoke test must not use the normal save path")
    store = StateStore(path)
    loaded = store.load_session()
    if not loaded.restored_from_save:
        satiety, energy = SCENARIOS[scenario]
        store.save(
            PetState(satiety=satiety, energy=energy),
            PetSettings(auto_walk=False, auto_routine=False, observe_computer=False,
                        learn_rhythm=False, spontaneous_talk=False),
            expected_revision=SaveRevision(), adaptive=AdaptiveMemory(),
            social_history=SocialContentHistory(),
        )
    if needs is not None:
        loaded = store.load_session()
        satiety, energy = SCENARIOS[needs]
        set_test_pet_values(loaded.state, satiety=satiety, energy=energy,
                            updated_at=time.time())
        store.save(loaded.state, loaded.settings, expected_revision=loaded.revision,
                   adaptive=loaded.adaptive_memory,
                   social_history=loaded.social_history,
                   world=loaded.world, object_memory=loaded.object_memory)
    return store


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=tuple(SCENARIOS), default="hungry")
    parser.add_argument("--save-path", type=Path)
    parser.add_argument("--needs", choices=tuple(SCENARIOS), help=(
        "Set only hunger/energy in this isolated test save; keep World and memory"
    ))
    parser.add_argument("--stock", choices=("one", "two"), help=(
        "Place one or two unknown Onigiri near Aiko in a fresh isolated save only"
    ))
    parser.add_argument("--auto-close-ms", type=int, default=0, help=argparse.SUPPRESS)
    args = parser.parse_args()
    path = args.save_path or (
        Path(tempfile.mkdtemp(prefix="aiko-world-smoke-")) / "state.sqlite3"
    )
    if args.stock is not None and (resolve_save_paths(path).database.exists()
                                   or resolve_save_paths(path).legacy_json.exists()):
        parser.error("--stock requires a fresh test save; "
                     "existing stock is not reseeded")
    print(f"Isolated World test save: {resolve_save_paths(path).database}", flush=True)
    print(f'Restart: python -m tools.world_smoke --save-path "{path}"', flush=True)
    if args.needs is not None:
        print(f"Explicit test need override: {args.needs}", flush=True)
    app = DesktopPet(store=prepare_session(
        path, scenario=args.scenario, needs=args.needs,
    ))
    if args.stock is not None:
        runtime = app._world
        image = runtime.view.image("onigiri", app.settings.scale)
        seed_stock(runtime.world, x=runtime._body_x(),
                   footprint=ObjectFootprint(image.width() / 2, image.width() / 2),
                   count=1 if args.stock == "one" else 2)
        app._save()
    if args.auto_close_ms > 0:
        app.root.after(args.auto_close_ms, app.quit)
    app.run()


if __name__ == "__main__":
    main()
