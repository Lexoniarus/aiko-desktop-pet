"""Build inspected Aiko 2x frame candidates from the original owner archives.

This is an offline export: no source art or Pillow is required by Aiko's runtime.
All output belongs to the owner-restricted Aiko art terms, not MIT.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.character_gaze_export import (  # noqa: E402
    gaze_foot_offset_x, left_gaze_scale_adjustment, register_gaze_row,
)
from tools.character_sleep_export import build_sleep_cycle  # noqa: E402

SIZE = (384, 416)
BASE = 'aiko-anime-compact/'
SKIP = {'running'}
STANDARD = {'idle', 'running-left', 'running-right', 'waving', 'jumping', 'failed', 'waiting', 'review'}
SOURCES = {key: 'source-frames/' + key for key in STANDARD}
SOURCES.update({key: key + '/frames-native' for key in ('sleep', 'petting', 'eat', 'attack')})
INTERMEDIATE = {
    'idle': {3: 'inbetweens/idle/generated/02-03.png', 5: 'inbetweens/idle/generated/03-04.png'},
    'waving': {1: 'inbetweens/waving/native/new-0-1-0.5.png', 3: 'inbetweens/waving/native/new-1-2-0.5.png', 5: 'inbetweens/waving/native/new-2-3-0.333.png', 6: 'inbetweens/waving/native/new-2-3-0.667.png'},
    'jumping': {1: 'inbetweens/jumping/generated/new-0-1.png', 4: 'inbetweens/jumping/generated/new-2-3.png', 6: 'inbetweens/jumping/generated/new-3-4.png'},
    'waiting': {2: 'inbetweens/waiting/generated/01-02.png', 4: 'inbetweens/waiting/generated/02-03.png'},
    'review': {2: 'inbetweens/review/generated/01-02.png', 5: 'inbetweens/review/generated/03-04.png'},
    'sleep': {2: 'inbetweens/sleep/generated/new-1-2.png', 5: 'inbetweens/sleep/generated/new-3-4.png'},
}


def decode(data: bytes) -> Image.Image:
    with Image.open(io.BytesIO(data)) as im:
        return im.convert('RGBA')


def alpha_box(image: Image.Image) -> tuple[int, int, int, int]:
    # Match the original app's 128 alpha threshold exactly.
    mask = image.getchannel('A').point([255 if i >= 128 else 0 for i in range(256)])
    b = mask.getbbox()
    if b is None:
        raise ValueError('Empty source/target frame')
    return b


def fit(source: Image.Image, reference: Image.Image) -> tuple[Image.Image, dict]:
    """Preserve the exact approved 1x placement and shoe baseline at 2x."""
    original_bbox, bbox = alpha_box(source), alpha_box(reference)
    source = source.crop(original_bbox)
    src_w, src_h = source.size
    rw, rh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    sx, sy = 2 * rw / src_w, 2 * rh / src_h
    width, height = 2 * rw, 2 * rh
    registered = source.resize((width, height), Image.Resampling.LANCZOS)
    output = Image.new('RGBA', SIZE, (0, 0, 0, 0))
    output.alpha_composite(registered, dest=(2*bbox[0], 2*bbox[1]))
    output.putalpha(output.getchannel('A').point([255 if i >= 128 else 0 for i in range(256)]))
    # Keep source and resulting sprite comparable in native coordinates.
    ref_mask = reference.getchannel('A').tobytes()
    reduced = output.getchannel('A').resize((192, 208), Image.Resampling.LANCZOS)
    hd_mask = reduced.tobytes()
    intersection = sum(r >= 128 and h >= 128 for r, h in zip(ref_mask, hd_mask))
    union = sum(r >= 128 or h >= 128 for r, h in zip(ref_mask, hd_mask))
    return output, {
        'source_bbox': list(original_bbox),
        'reference_bbox': list(bbox),
        'aspect_rescale_ratio': round(sx/sy, 4),
        'silhouette_iou': round(intersection/union, 4),
    }


def source_frame(z: zipfile.ZipFile, st: str, idx: int, kind: str, source_index: int|None) -> tuple[Image.Image, str, str]:
    if kind == 'original':
        if source_index is None:
            raise ValueError(f'Missing original index: {st}/{idx}')
        file = f'{SOURCES[st]}/{source_index:02d}.png' if st in STANDARD else f'{SOURCES[st]}/{source_index+1:02d}.png'
        status = 'original_hd'
    else:
        file = INTERMEDIATE[st][idx]
        status = 'generated_intermediate_hd'
    try:
        image = decode(z.read(BASE + file))
        image.load()
    except (OSError, ValueError):
        # Two upstream PNGs have truncated IDAT. Their original HD contact
        # sequences preserve both complete poses without invented art.
        if (st,idx)==('review',1):
            sheet='decoded/review.png'
            original=decode(z.read(BASE+sheet))
            cell=(round(original.width/6),0,round(original.width*2/6),original.height)
            return original.crop(cell),f'{sheet}#tile=1','recovered_original_hd_sheet'
        if (st,idx)==('eat',7):
            sheet='eat/eat-source-equal-slots.png'
            original=decode(z.read(BASE+sheet))
            cell=(round(original.width*7/8),0,original.width,original.height)
            return original.crop(cell),f'{sheet}#tile=7','recovered_original_hd_sheet'
        raise RuntimeError(f'No complete HD original available: {st}/{idx}')
    return image, file, status


def gaze_frames(z: zipfile.ZipFile, gazedata: dict) -> list[tuple]:
    """Register all native connected gaze poses proportionally by their feet."""
    frames = []
    rows = ('decoded/look-row-9.png', 'decoded/look-row-10-before-registration.png')
    for part, row in enumerate(rows):
        image = decode(z.read(BASE+row))
        references = [
            decode(z.read(BASE+'animations-8/look-directions/'+item['file']))
            for item in gazedata['directions'][part*8:(part+1)*8]
        ]
        registered = register_gaze_row(
            image, references,
            scale_adjustments=[left_gaze_scale_adjustment(part*8+i) for i in range(8)],
            horizontal_offsets=[gaze_foot_offset_x(part*8+i) for i in range(8)],
        )
        for i, (result, info) in enumerate(registered):
            source = f'{row}#component={i}'
            frames.append((result, source, info))
    return frames


def export(archive:Path,pickup_archive:Path,target:Path) -> dict:
    target.mkdir(parents=True,exist_ok=True)
    generated=[]
    with zipfile.ZipFile(archive) as z, zipfile.ZipFile(pickup_archive) as pp:
        prov=json.loads(z.read(BASE+'animations-8/provenance.json'))
        for record in prov:
            state=record['state'];i=record['frame']-1
            if state in SKIP or state == 'sleep':continue
            lo=decode(z.read(f'{BASE}animations-8/{state}/frames/{i+1:02d}.png'))
            high,source,status=source_frame(z,state,i,record['kind'],record.get('source_index'))
            rel=f'{state}/{i:02d}.png'
            result,info=fit(high,lo)
            generated.append((rel,source,status,result,info))
        # Rebuild the approved stationary-bed cycle from two complete HD
        # originals. Raw generated intermediates move the character and bed.
        rest_source = 'sleep/frames-native/01.png'
        raised_source = 'sleep/frames-native/04.png'
        rest, rest_info = fit(
            decode(z.read(BASE+rest_source)),
            decode(z.read(BASE+'animations-8/sleep/frames/01.png')),
        )
        raised, raised_info = fit(
            decode(z.read(BASE+raised_source)),
            decode(z.read(BASE+'animations-8/sleep/frames/05.png')),
        )
        cycle = build_sleep_cycle(rest, raised)
        for i, result in enumerate(cycle.frames):
            info = {
                'aspect_rescale_ratio': None, 'silhouette_iou': None,
                'fixed_base_source': rest_source,
                'blanket_peak_source': raised_source,
                'base_registration': rest_info,
                'blanket_registration': raised_info,
                'blanket_blend_factor': cycle.factors[i],
                'blanket_mask_bbox': list(cycle.mask.getbbox()),
            }
            generated.append((f'sleep/{i:02d}.png',
                              f'{rest_source}#blanket={raised_source}',
                              'original_hd_fixed_base_blanket_cycle', result, info))
        for i in range(8):
            lo=decode(pp.read(f'Laufzeit_192x208/{i+1:02d}.png'))
            high=decode(pp.read(f'Registriert_Hochaufloesend/{i+1:02d}.png'))
            result,info=fit(high,lo)
            generated.append((f'pick_up/{i:02d}.png',f'Registriert_Hochaufloesend/{i+1:02d}.png','original_hd_pickup',result,info))
        gazedata=json.loads(z.read(BASE+'animations-8/look-directions/directions.json'))
        for i, (result, source, info) in enumerate(gaze_frames(z, gazedata)):
            generated.append((f'look/{i:02d}.png',source,'original_hd_gaze_atlas',result,info))
    generated.sort(key=lambda x:x[0])
    if len(generated)!=120 or len({x[0] for x in generated})!=120:
        raise ValueError(f'Expected 120 unique Aiko poses, received {len(generated)}')
    files=[]
    for rel,source,status,image,info in generated:
        dst=target/rel;dst.parent.mkdir(parents=True,exist_ok=True)
        # Preserve existing encodings when only unrelated poses are rebuilt.
        # PNG compression can differ between platforms despite identical RGBA.
        same_pixels = False
        if dst.is_file():
            try:
                with Image.open(dst) as existing:
                    same_pixels = (existing.size == image.size
                                   and existing.convert('RGBA').tobytes() == image.tobytes())
            except OSError:
                pass
        if not same_pixels:
            image.save(dst,optimize=True)
        record={'path':rel,'source':source,'status':status,'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(), **info,'bytes':dst.stat().st_size}
        files.append(record)
    archive_sha=hashlib.sha256(archive.read_bytes()).hexdigest()
    pickup_sha=hashlib.sha256(pickup_archive.read_bytes()).hexdigest()
    manifest={'version':1,'size':list(SIZE),'source_archive_sha256':archive_sha,'pickup_archive_sha256':pickup_sha,'frames':files}
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    with (target.parent/'aiko_hd_2x_audit.csv').open('w',newline='',encoding='utf-8-sig') as f:
        fields = list(dict.fromkeys(key for record in files for key in record))
        out=csv.DictWriter(f,fieldnames=fields);out.writeheader();out.writerows(files)
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--source-archive',type=Path,required=True)
    parser.add_argument('--pickup-archive',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    manifest=export(args.source_archive,args.pickup_archive,args.output_dir)
    from collections import Counter
    print(json.dumps(dict(total=len(manifest['frames']),status=dict(Counter(i['status'] for i in manifest['frames'])),avg_bytes=round(sum(i['bytes'] for i in manifest['frames'])/len(manifest['frames'])),sum_bytes=sum(i['bytes'] for i in manifest['frames']),low_iou=[(i['path'],i['silhouette_iou']) for i in manifest['frames'] if i['silhouette_iou'] is not None and i['silhouette_iou']<0.85],high_distortion=[(i['path'],i['aspect_rescale_ratio']) for i in manifest['frames'] if i['aspect_rescale_ratio'] is not None and (i['aspect_rescale_ratio']>1.25 or i['aspect_rescale_ratio']<.8)]),indent=2))
