"""Repeated restored sessions release Tk image owners before any later GC."""

import tempfile
import tkinter as tk
import unittest
import weakref
from pathlib import Path

from aiko_pet.gui import DesktopPet
from aiko_pet.infrastructure.persistence import StateStore
from aiko_pet.world.contracts import ObjectFootprint


class WorldAssetShutdownTests(unittest.TestCase):
    def test_quit_releases_all_image_owners_while_app_is_still_referenced(self):
        try:
            probe = tk.Tk()
            probe.destroy()
        except tk.TclError as error:
            self.skipTest(str(error))
        with tempfile.TemporaryDirectory() as folder:
            app = DesktopPet(store=StateStore(Path(folder) / "state.json"))
            self.addCleanup(app.quit)
            animated = app._animated
            original = weakref.ref(animated.sprites["idle"][0])
            food = weakref.ref(animated.food_overlay._images[("onigiri", 1)])
            app.settings.scale = 2
            animated.reload_sprites()
            zoomed = weakref.ref(animated.sprites["idle"][0])
            warped = weakref.ref(animated._rest_renderer.resolve(
                animated.sprites["idle"][0], offset=1, scale=2,
            ))
            app._world.world.place_resting("onigiri", app._world._body_x(),
                                           ObjectFootprint(16, 16))
            app._world._sync_view()
            ground = weakref.ref(app._world.view.image("onigiri", 2))
            images = original, food, zoomed, warped, ground
            self.assertTrue(all(reference() is not None for reference in images))
            app.quit()
            # No gc.collect(), process exit or loss of the app reference needed.
            self.assertTrue(all(reference() is None for reference in images))
            animated.close()
            app.quit()
