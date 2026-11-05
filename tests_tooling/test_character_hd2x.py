"""Pure HD registration tests; no external original ZIP is required in CI."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from PIL import Image

from tools.build_character_hd2x import compose_registered, prepare_pickup


class CharacterHd2xTests(unittest.TestCase):
    def test_registered_output_keeps_runtime_footprint_and_true_hd_rgb(self) -> None:
        large = Image.new("RGBA", (1024, 1536))
        for x in range(250, 650):
            for y in range(180, 1180):
                large.putpixel((x, y), (23, 65, 109, 255))
        small = Image.new("RGBA", (192, 208))
        small.paste((2, 3, 4, 255), (60, 25, 140, 193))
        out = compose_registered(large, small)
        self.assertEqual(out.size, (384, 416))
        self.assertEqual(out.getchannel("A").getbbox(), (120, 50, 280, 386))
        self.assertEqual(out.getpixel((180, 160)), (23, 65, 109, 255))

    def test_rejects_missing_or_invalid_source(self) -> None:
        large = Image.new("RGBA", (1024, 1536), (1, 2, 3, 255))
        small = Image.new("RGBA", (191, 208), (1, 2, 3, 255))
        with self.assertRaisesRegex(ValueError, "192x208"):
            compose_registered(large, small)

    def test_complete_bundle_exports_exactly_eight_frames(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            original = base / "original.zip"
            hd = Image.new("RGBA", (1024, 1536), (50, 100, 150, 255))
            native = Image.new("RGBA", (192, 208))
            native.paste((20, 30, 40, 255), (65, 35, 135, 196))
            import io

            def png_bytes(image: Image.Image) -> bytes:
                payload = io.BytesIO()
                image.save(payload, "PNG")
                return payload.getvalue()

            with ZipFile(original, "w") as archive:
                for i in range(1, 9):
                    archive.writestr(
                        f"Registriert_Hochaufloesend/{i:02}.png",
                        png_bytes(hd),
                    )
                    archive.writestr(
                        f"Laufzeit_192x208/{i:02}.png",
                        png_bytes(native),
                    )
            outputs = prepare_pickup(original, base / "out")
            self.assertEqual(len(outputs), 8)
            self.assertEqual([path.name for path in outputs],
                             [f"{i:02}.png" for i in range(8)])
            with Image.open(outputs[0]) as prepared:
                self.assertEqual(prepared.size, (384, 416))


if __name__ == "__main__":
    unittest.main()
