# Offline character exporters

These development tools install reviewed artwork. They do not generate art,
run inside Aiko or add dependencies to the application. Pillow is a build/test
dependency only. Private originals, source packages and diagnostic snapshots
remain outside Git.

| Command | Input | Output scope |
| --- | --- | --- |
| `python -m tools.character_eating_export ORIGINALS --hd-root HD_ROOT` | Seven large eating originals | Eight `eat` slots |
| `python -m tools.character_gaze_modular_export PACKAGE --hd-root HD_ROOT` | Reviewed shared-body gaze package | Sixteen `look` slots |
| `python -m tools.character_idle_modular_export PACKAGE --hd-root HD_ROOT` | Reviewed eye-only blink package | Eight `idle` slots |
| `python -m tools.character_request_export PACKAGE --hd-root HD_ROOT` | Reviewed question/request gesture package | Eight `waiting` slots |
| `python -m tools.character_body_pose_export PACKAGE ASSET_ROOT` | Reviewed body/head/turn package | Separate optional `body_poses` pack |

The first four commands update only their HD frames and corresponding records
in the existing HD manifest. The body exporter leaves both atlases untouched.
Run the base atlas preparation before applying replacements. Existing approved
outputs remain unchanged by this tool cleanup; no asset installation is needed
to run the synthetic exporter tests.

`tools.character_export_common` owns the shared HD dimensions, binary alpha
threshold, PNG decoding, content digests and planted-foot measurement. Exporters
import these contracts directly instead of importing each other's CLI modules.
Frame registration and package-specific validation stay with their exporter.

Each exporter validates its complete source set and encodes every output in a
temporary staging directory before publishing files. Individual replacements
use `os.replace`; the manifest is published last. This protects an existing
installation from missing/invalid inputs and PNG encoding failures. Publication
is not a filesystem transaction: an interrupted replacement still requires
rerunning the export. Do not export into an installation while Aiko is running.

The obsolete full-figure V3 gaze algorithm and its tests are preserved privately
and are excluded from the active tool set. Reapplying that algorithm would
replace the approved shared-body gaze images. Earlier V2 archive tools remain
available for their original inputs; their registration rules do not apply to
the modular V3 packages.

Synthetic package tests exercise complete installation, protected pixels,
provenance checks and failure without partial publication. Tests of the shipped
catalogue and renderer belong to the corresponding asset/runtime changes.
