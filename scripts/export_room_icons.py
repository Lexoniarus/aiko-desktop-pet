"""Derive Home Screen icons from the already approved runtime idle artwork."""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    source = ROOT / "aiko_pet/assets/frames_2x/idle/00.png"
    with Image.open(source) as original:
        original = original.convert("RGBA")
        for size in (192, 512):
            icon = Image.new("RGBA", (size, size), "#f7f2f3")
            figure = original.copy()
            figure.thumbnail(
                (int(size * 0.85), int(size * 0.92)), Image.Resampling.LANCZOS
            )
            icon.alpha_composite(
                figure, ((size - figure.width) // 2, (size - figure.height) // 2)
            )
            icon.convert("RGB").save(ROOT / f"web/public/icon-{size}.png")


if __name__ == "__main__":
    main()
