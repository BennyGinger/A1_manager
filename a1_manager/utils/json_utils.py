from __future__ import annotations # Enable type annotation to be stored as string
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .utility_classes import StageCoord, WellCircleCoord, WellSquareCoord

def encode_dataclass(obj: Any) -> Any:
    """Encode a dataclass object into a dictionary with the __class__ attribute to be able to decode it later.
    
    If the object is naturally JSON serializable (e.g. dict, list, str, int, float, bool, or None),
    it is returned without modification.
    """
    
    if isinstance(obj, (dict, list, str, int, float, bool, type(None))):
        return obj
    if hasattr(obj, '__dataclass_fields__'):
        data = asdict(obj)
        data["__class__"] = obj.__class__.__name__
        return data
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

# Custom decoder function
def decode_dataclass(data: dict) -> WellCircleCoord | WellSquareCoord | StageCoord | dict:
    """Decode a dictionary into a dataclass object."""
    
    if "__class__" in data:
        cls_name = data.pop("__class__")
        
        # Convert all lists to tuples
        data = {k: (tuple(v) if isinstance(v, list) else v) for k, v in data.items()}
        
        # Return the decoded dataclass object
        if cls_name == "WellSquareCoord":
            return WellSquareCoord(**data)
        elif cls_name == "WellCircleCoord":
            return WellCircleCoord(**data)
        elif cls_name == "StageCoord":
            return StageCoord(**data)
    return data


def load_config_file(calib_path: Path) -> dict[str, WellCircleCoord | WellSquareCoord]:
    """
    Load the calibration file which contains the dish measurements, including the focus values.
    
    Args:
        calib_path (Path): Path to the calibration JSON file
        
    Returns:
        dict[str, WellCircleCoord | WellSquareCoord]: Dictionary mapping well names to well coordinate objects
    """
    with open(calib_path) as f:
        raw = json.load(f)
    result = {}
    for well, data in raw.items():
        if 'radius' in data and 'center' in data:
            allowed_keys = WellCircleCoord.__dataclass_fields__.keys()
            filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
            result[well] = WellCircleCoord(**filtered_data)
        else:
            allowed_keys = WellSquareCoord.__dataclass_fields__.keys()
            filtered_data = {k: v for k, v in data.items() if k in allowed_keys}
            result[well] = WellSquareCoord(**filtered_data)
    return result


def save_config_file(calib_path: Path, data: dict) -> None:
    """
    Update the calibration file with the new focus values.
    
    Args:
        calib_path (Path): Path to the calibration JSON file
        data (dict): Dictionary of well coordinate objects to save
    """
    serializable = {k: asdict(v) for k, v in data.items()}
    with open(calib_path, 'w') as f:
        json.dump(serializable, f)