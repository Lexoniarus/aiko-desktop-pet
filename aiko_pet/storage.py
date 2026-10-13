"""Legacy persistence import path; real JSON repository lives in infrastructure.

The shim preserves external imports without implementing a parallel StateStore.
"""

from __future__ import annotations

import json as json
import os as os
import sys as sys
import tempfile as tempfile
import time as time
from pathlib import Path as Path

from .infrastructure.persistence import (
    SCHEMA_VERSION as SCHEMA_VERSION,
    PetSettings as PetSettings,
    StateStore as StateStore,
    default_save_path as default_save_path,
)
