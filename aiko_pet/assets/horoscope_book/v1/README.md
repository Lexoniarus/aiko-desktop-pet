# Enchanted violet horoscope book — V1

Four transparent book-only states in the owner-approved Aiko-style violet
design. See the [asset and lifecycle contract](../../../../docs/HOROSCOPE_BOOK_ASSETS.md)
for intended use, geometry, source handling and implementation scope.

- [Manifest: states, sizes, paths and book-local pivots](manifest.json)
- [Provenance: native selection and exported-file hashes](provenance.json)
- [Exact Imagegen prompt history](prompts.json)
- [Asset validation and independent-review summary](validation.json)

`rgba/1x` and `rgba/2x` contain smooth-alpha images. `display/1x` and
`display/2x` contain alpha-128 binary copies for Windows color-key rendering.
`icons/32.png` and `icons/64.png` are menu thumbnails. Carried-state pivots are
shared at 48,64 on96x80 at1x and doubled at2x; placement uses32,40 on64x48.
The manifest is descriptive asset metadata, with `runtime_registered: false`.

The four selected native filenames are `closed_world.png`, `carry_closed.png`,
`half_open-02.png` and `open_reading-02.png`. Full-resolution originals remain
in the private authoring run identified by provenance. Existing project asset
origin and terms are unchanged. This pack supplies no new character frames.
