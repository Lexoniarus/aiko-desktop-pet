"""Canonical paths for packaged sprites, emotes and Kenney interface assets."""

from pathlib import Path

ASSET_ROOT = Path(__file__).resolve().parent / "assets"
SPRITE_FRAME_DIR = ASSET_ROOT / "frames"
EMOTE_IMAGE_DIR = ASSET_ROOT / "emotes"
KENNEY_UI_DIR = ASSET_ROOT / "kenney_ui"

# Asset names used by the concrete character and speech views.
ASSETS = SPRITE_FRAME_DIR
EMOTE_ASSETS = EMOTE_IMAGE_DIR
SCI_FI_UI = KENNEY_UI_DIR
