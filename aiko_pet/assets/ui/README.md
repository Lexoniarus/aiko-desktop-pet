# Packaged VN interface exports

Development export: `python tools/export_vn_ui.py` (Pillow is development-only).
Original UI masters and provenance remain in `assets/ui-vn/v1`; runtime never
loads full-resolution masters or the external preview bundle. `catalog.json`
records all 54 selected source hashes and the exported icon/control paths.

Icons are optically cropped at alpha 8, padded and exported at 24/32/40/48/64/
96/128 pixels (including 1x/2x sizes). Alpha remains antialiased. Five blank
button states use shared cap-preserving slices at the actual control sizes;
status track/rim exports remain separate from dynamic UI fills. Text, concrete
wish targets, badges and focus outlines are composed separately.

`ui/common/icon_images.py::IconImages` owns one root-local Tk cache and releases it on the owner
thread. There is no runtime Pillow dependency, sprite replacement, extra font
bundle, domain tuning or new license assignment. The original OpenAI Imagegen
provenance and existing Kenney playing-card/license notices remain applicable.
Export/pixel checks do not establish native Windows visual/input acceptance.
