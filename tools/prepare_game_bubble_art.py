"""Export the approved VN panel for color-keyed game speech; RGB is preserved."""
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def prepare() -> None:
    directory = ROOT / 'aiko_pet/assets/ui'
    source = directory / 'panel_surface_panel.png'
    target = directory / 'game_bubble_panel.png'
    with Image.open(source) as original:
        image = original.convert('RGBA')
        rgb = image.convert('RGB').tobytes()
        image.putalpha(image.getchannel('A').point([0] * 128 + [255] * 128))
        assert image.convert('RGB').tobytes() == rgb
        image.save(target, optimize=True)
    record = dict(source=source.relative_to(ROOT).as_posix(),
                  source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  target=target.relative_to(ROOT).as_posix(),
                  sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                  method='Binary alpha for Windows color key; original RGB unchanged')
    (ROOT / 'aiko_pet/assets/game_frontends/game-bubble-provenance.json').write_text(
        json.dumps(record, indent=2) + '\n', encoding='utf-8',
    )


if __name__ == '__main__':
    prepare()
