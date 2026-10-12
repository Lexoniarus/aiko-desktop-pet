# Asset provenance, licensing, and acknowledgments

This repository includes original project content, AI-generated character artwork, and third-party Kenney game assets. Their origins are documented separately.

## 1. Project source code — MIT

Unless a file identifies a different license, the project's own source code is distributed under the [MIT License](LICENSE). MIT permits copying, modification, redistribution, sublicensing, and commercial use, subject to preserving the required copyright and license notices. Public availability is not an additional usage restriction.

## 2. Aiko character artwork and animation sprites — MIT

The **73 Aiko character animation frames** under `aiko_pet/assets/frames/` were prepared from the project's original generated artwork. According to the project creator, the artwork was produced with **OpenAI image-generation tools through a Codex-based generation workflow**, with subsequent selection, layout preparation, and sprite extraction.

The creator makes any **licensable rights the creator controls** in these project-authored image assets available under the project's [MIT License](LICENSE). These assets are therefore **not** subject to a separate proprietary reuse restriction in this repository.

The technical provenance manifest is `aiko_pet/assets/provenance.json`. It identifies the source sheet, source hash, sprite counts, and cropping parameters. The extraction step did not invent additional character poses.

OpenAI's [Terms of Use](https://openai.com/policies/terms-of-use/) address ownership of generated output as between the user and OpenAI, to the extent permitted by applicable law. They do not impose a special “Codex desktop-pet sprite license” for these images. AI-generated output might not be unique or copyright-protected in every jurisdiction; this notice does not claim exclusivity over all generated content, imply endorsement by OpenAI, or grant rights the project creator does not possess.

## 3. Kenney game assets — CC0 1.0

The project uses artwork from these Kenney asset packs:

- **Kenney Emote Pack (1.0):** pixel emotes under `aiko_pet/assets/emotes/`.
- **Kenney UI Pack: Sci-fi (2.0):** source and adapted panel/button graphics under `aiko_pet/assets/kenney_ui/`.

The creator obtained the assets through a **paid Kenney Game Assets All-in-1 3.4.0 bundle**. The license files supplied with the packs identify the artwork as **Creative Commons Zero (CC0 1.0)**. Purchasing the bundle does not change those CC0 terms.

**Credit: Game assets by [Kenney](https://kenney.nl/).** Attribution is not required under the included CC0 license, but is voluntarily provided and appreciated.

See [LICENSES/KENNEY_CC0.md](LICENSES/KENNEY_CC0.md) and the [CC0 1.0 legal text](https://creativecommons.org/publicdomain/zero/1.0/).

The repository's MIT notice does **not** replace Kenney's CC0 designation.

## 4. Optional fonts

The user-supplied `Kenney Mini.ttf` is **not distributed** with the project. Aiko uses a compatible font already installed on the user's computer when available, or falls back to Segoe UI. Third-party fonts remain subject to their own terms; the project's MIT license does not relicense a font installed separately.

## 5. Screenshots and previews

Images in `vorschau/` may contain both Aiko sprite art and Kenney UI/emotes. Their depicted components retain the license and provenance described above.

## 6. Language

Documentation is maintained in **English**. UI strings, dialog entries, and runtime labels deliberately remain in **German** for the current game release.
