# Aiko Anime runtime source export

Only the **134 original inputs used to rebuild the selected character export**
from `Aiko_Anime_8_Frames_Komplett.zip` are tracked, byte-for-byte, with their
archive paths preserved. These are 120 pose/hand-layer PNGs, twelve animation
manifests, the animation catalog and the gaze-direction manifest.

The other **813 archive members** remain local and are ignored by Git:
references, generation attempts, prompts, QA, preview animations, contact
sheets and original preparation scripts. The ZIP is not duplicated in Git.
No imported scripts are executed.

The desktop export is
`aiko-anime-compact/animations-8/catalog.json`: 12 selected eight-frame animation clips
and 16 cursor-gaze poses, all on 192 × 208 pixel canvases. Attack is retained
for future use and has no application trigger. Food, weapon and spell graphics
are not included; their optional anchors remain in the manifests.

The application loads prepared copies under `aiko_pet/assets/frames/` and the
typed runtime catalog in `aiko_pet/assets/animations.json`. Rebuild these with
`python tools/prepare_character_assets.py`. This preparation keeps full image
width and applies the existing binary-alpha policy for Windows transparency;
the original imported images remain unchanged.

Runtime metadata records original frame durations as `source_duration_ms` and
applies the application's 2.52-second ambient and 1.413-second walking profile.
Other clips retain their source timing; no original manifests are modified.

See [the asset terms](LICENSE.md) for the new artwork's restricted reuse.
Application and preparation code remain MIT; Kenney artwork remains CC0.
[IMPORT_MANIFEST.json](IMPORT_MANIFEST.json) records the source ZIP checksum,
the paths, byte sizes and SHA-256 hashes of the included original inputs.
Its inventory excludes unused archive members and these repository-added
notices. Ignore rules admit only the selected export's manifests and poses.

The generic `running` clip has no application caller and is excluded. The
source catalog is preserved unchanged; preparation selects directional walking
and skips the unused generic clip.
