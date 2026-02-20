from __future__ import annotations # Enable type annotation to be stored as string
import logging

import json
from pathlib import Path
from tifffile import imwrite
from time import sleep
from typing import Any

from a1_manager.microscope_hardware.nanopick.injection_factory import Injection
from a1_manager import A1Manager

# Set up logging
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    