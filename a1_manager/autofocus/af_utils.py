from __future__ import annotations # Enable type annotation to be stored as string
import json
from pathlib import Path
import numpy as np
from typing import Optional


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


def prompt_autofocus_with_image(image: np.ndarray, use_gui: bool = True) -> None:
    """
    Show autofocus image and ask user whether to continue, restart, or quit.
    
    Args:
        image (np.ndarray): The captured image to display for focus evaluation
        use_gui (bool): Whether to use GUI (True) or fallback to terminal (False)
        
    Raises:
        QuitAutofocus: If user chooses to quit
        RestartAutofocus: If user chooses to restart
    """
    if use_gui:
        try:
            from .autofocus_gui import prompt_autofocus_gui, AutofocusResult
            result = prompt_autofocus_gui(image, "Current Focus")
            
            if result == AutofocusResult.QUIT:
                raise QuitAutofocus
            elif result == AutofocusResult.RESTART:
                raise RestartAutofocus
            # Continue case - just return normally
            return
            
        except ImportError as e:
            print(f"⚠️  GUI not available ({e}). Using terminal prompt.")
        except (QuitAutofocus, RestartAutofocus):
            # Re-raise these exceptions - they are expected
            raise
        except Exception as e:
            print(f"⚠️  GUI failed ({e}). Using terminal prompt.")
    
    # Fallback to terminal prompt
    try:
        prompt_autofocus("\nIf focus is good press Enter, else type 'r' to restart or 'q' to quit: ")
    except (QuitAutofocus, RestartAutofocus):
        # Re-raise these exceptions - they are expected
        raise