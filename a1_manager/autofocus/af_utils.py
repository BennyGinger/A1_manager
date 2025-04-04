from __future__ import annotations # Enable type annotation to be stored as string
import json
from pathlib import Path

#TODO: Note form Raph: Is this method meant to be also called from the user? If not, we can make it private.
def load_config_file(calib_path: Path)-> dict:
    """Load the calibration file which contains the dish measurements, including the focus values."""
    with open(calib_path) as f:
        return json.load(f)

#TODO: Note form Raph: Is this method meant to be also called from the user? If not, we can make it private.
def save_config_file(calib_path: Path, data: dict)-> None:
    """Update the calibration file with the new focus values."""
    with open(calib_path,'w') as f:
        json.dump(data,f)
