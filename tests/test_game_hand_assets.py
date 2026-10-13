"""Validate tiny, bundled PNG emoji graphics without imaging dependencies."""

from __future__ import annotations

import struct
import unittest
import zlib

from aiko_pet.asset_paths import GAME_HANDS_DIR


def read_png_chunks(raw: bytes) -> list[bytes]:
    """Reject truncated files and invalid CRCs before Tk tries to decode them."""
    if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Missing PNG signature")
    chunks: list[bytes] = []
    cursor = 8
    while cursor < len(raw):
        if len(raw) - cursor < 12:
            raise ValueError("Incomplete PNG chunk header")
        length = struct.unpack(">I", raw[cursor:cursor + 4])[0]
        end = cursor + 12 + length
        if length > 100_000 or end > len(raw):
            raise ValueError("Invalid PNG chunk length")
        chunk_type = raw[cursor + 4:cursor + 8]
        chunk_data = raw[cursor + 8:end - 4]
        checksum = struct.unpack(">I", raw[end - 4:end])[0]
        if zlib.crc32(chunk_type + chunk_data) != checksum:
            raise ValueError("Invalid PNG chunk CRC")
        chunks.append(chunk_type)
        cursor = end
        if chunk_type == b"IEND":
            break
    if cursor != len(raw) or not chunks or chunks[-1] != b"IEND":
        raise ValueError("PNG must finish at IEND")
    return chunks


class GameHandAssetsTests(unittest.TestCase):
    def test_each_light_tone_emoji_is_a_complete_color_png(self) -> None:
        for name in ("rock", "paper", "scissors"):
            with self.subTest(name=name):
                path = GAME_HANDS_DIR / f"{name}.png"
                raw = path.read_bytes()
                self.assertLess(len(raw), 10_000)
                self.assertEqual(raw[12:16], b"IHDR")
                self.assertEqual(
                    struct.unpack(">II", raw[16:24]), (72, 72),
                )
                chunks = read_png_chunks(raw)
                self.assertIn(b"PLTE", chunks)
                self.assertIn(b"tRNS", chunks)

    def test_corrupted_crc_is_rejected(self) -> None:
        raw = bytearray((GAME_HANDS_DIR / "rock.png").read_bytes())
        raw[60] ^= 1
        with self.assertRaises(ValueError):
            read_png_chunks(bytes(raw))


if __name__ == "__main__":
    unittest.main()
