"""Canonical paths for packaged sprites, emotes and Kenney interface assets."""

from pathlib import Path

ASSET_ROOT = Path(__file__).resolve().parent / "assets"
SPRITE_FRAME_DIR = ASSET_ROOT / "frames"
EMOTE_IMAGE_DIR = ASSET_ROOT / "emotes"
KENNEY_UI_DIR = ASSET_ROOT / "kenney_ui"

GAME_HANDS_DIR = ASSET_ROOT / "game_hands"
PLAYING_CARDS_DIR = ASSET_ROOT / "playing_cards"
CONNECT_FOUR_DIR = ASSET_ROOT / "connect_four"
