"""Preview files remain readable without pinning an old gallery layout."""

import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class CurrentGalleryTests(unittest.TestCase):
    def test_gallery_images_are_readable_and_gifs_are_animated(self):
        files = tuple(path for path in (ROOT / "vorschau").iterdir()
                      if path.suffix.lower() in {".png", ".gif"})
        self.assertTrue(files)
        for path in files:
            with self.subTest(file=path.name), Image.open(path) as media:
                self.assertGreater(min(media.size), 0)
                if path.suffix.lower() == ".gif":
                    self.assertGreater(getattr(media, "n_frames", 1), 1)
                media.verify()
