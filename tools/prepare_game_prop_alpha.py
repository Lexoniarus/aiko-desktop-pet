"""Prepare color-keyed Windows game overlays without changing source RGB.

Developer-only Pillow export; original illustration sources remain outside Git.
Opaque game-board backgrounds and controls retain their antialiased alpha.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1] / 'aiko_pet' / 'assets' / 'game_frontends'


def prepare() -> None:
    manifest = ROOT / 'native-prop-alpha.json'
    records = json.loads(manifest.read_text('utf-8')) if manifest.exists() else {}
    targets = [*sorted((ROOT / 'mm-safe').glob('*.png')),
               *sorted((ROOT / 'c4-hands').glob('*.png')),
               *(ROOT / name for name in ('c4-red.png', 'c4-yellow.png',
                                         'c4-pile.png', 'mm-donut.png',
                                         'quiz-cues.png'))]
    for path in targets:
        if not path.exists():
            continue
        relative = path.relative_to(ROOT).as_posix()
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        if records.get(relative, {}).get('sha256') == before:
            continue
        with Image.open(path) as original:
            image = original.convert('RGBA')
            rgb = image.convert('RGB').tobytes()
            image.putalpha(image.getchannel('A').point(
                [0] * 128 + [255] * 128,
            ))
            assert image.convert('RGB').tobytes() == rgb
            image.save(path, optimize=True)
        records[relative] = dict(
            raster_sha256=before, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            rgb_unchanged=True, alpha='0 or255; threshold128',
        )
    manifest.write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')
    for name, field in (('mm-provenance.json', 'frames'),
                        ('c4-provenance.json', 'exports'),
                        ('quiz-provenance.json', 'exports')):
        path = ROOT / name
        if not path.exists():
            continue
        data = json.loads(path.read_text('utf-8'))
        for entry in data[field]:
            relative = entry.get('file', entry.get('target', entry.get('filename')))
            if relative in records:
                entry.update(records[relative])
        data['native_alpha'] = 'native-prop-alpha.json; all RGB preserved'
        path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    prepare()
