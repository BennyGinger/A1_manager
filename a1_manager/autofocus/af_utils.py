from __future__ import annotations # Enable type annotation to be stored as string
import json
from pathlib import Path


def load_config_file(calib_path: Path)-> dict:
    """Load the calibration file which contains the dish measurements, including the focus values."""
    with open(calib_path) as f:
        return json.load(f)

def save_config_file(calib_path: Path, data: dict)-> None:
    """Update the calibration file with the new focus values."""
    with open(calib_path,'w') as f:
        json.dump(data,f)


class QuitAutofocus(Exception):
    """Raised when the user wants to quit autofocus altogether."""
    pass

class RestartAutofocus(Exception):
    """Raised when the user wants to restart the autofocus scan."""
    pass


def prompt_autofocus(prompt: str) -> None:
    """
    Ask the user whether to continue, restart, or quit.
    Raises:
      - QuitAutofocus if they type 'q'
      - RestartAutofocus if they type 'r'
      - (nothing) if they press Enter
    """
    resp = input(prompt).strip().lower()
    if resp == 'q':
        raise QuitAutofocus
    if resp == 'r':
        raise RestartAutofocus