from __future__ import annotations # Enable type annotation to be stored as string
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from a1_manager import CONFIG_DIR
from a1_manager.utils.utility_classes import StageCoord, WellCircleCoord, WellSquareCoord

logger = logging.getLogger(__name__)


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

def load_config_file(file: Path | str) -> dict[str, Any] | None:
    """
    Load the calibration file which contains the dish measurements, including the focus values.
    
    Args:
        file (Path | str): Path or filename to the calibration JSON file

    Returns:
        dict[str, Any] | None: Dictionary mapping well names to well coordinate objects. Returns None if the file is not found.
    """
    if isinstance(file, Path):
        file_path = file
    elif isinstance(file, str):
        found_file = None
        for f in CONFIG_DIR.iterdir():
            if f.match(f"*{file}*"):
                found_file = f
                break
        if found_file is None:
            logger.warning(f"No file matching '{file}' found in {CONFIG_DIR}.")
            return None
        file_path = found_file
    else:
        raise TypeError("file must be a Path or str")
    
    with open(file_path) as f:
        raw_data = json.load(f, object_hook=decode_dataclass)
    
    # Convert legacy format (plain dicts) to dataclass objects
    if raw_data is None:
        return None
        
    result = {}
    for well_name, well_data in raw_data.items():
        if isinstance(well_data, dict):
            # Check if this looks like coordinate data (has center/radius or coordinate fields)
            is_coordinate_data = (
                ('radius' in well_data and 'center' in well_data) or  # CircleCoord
                ('top_left' in well_data or 'bottom_right' in well_data) or  # SquareCoord
                ('ZDrive' in well_data or 'PFSOffset' in well_data) or  # Any well coord
                ('xy' in well_data or 'z' in well_data)  # StageCoord
            )
            
            if is_coordinate_data:
                # Legacy format - convert to appropriate dataclass
                if 'radius' in well_data and 'center' in well_data:
                    # It's a circular well
                    allowed_keys = WellCircleCoord.__dataclass_fields__.keys()
                    filtered_data = {k: v for k, v in well_data.items() if k in allowed_keys}
                    # Convert list to tuple for center if needed
                    if 'center' in filtered_data and isinstance(filtered_data['center'], list):
                        filtered_data['center'] = tuple(filtered_data['center'])
                    result[well_name] = WellCircleCoord(**filtered_data)
                elif 'xy' in well_data or 'z' in well_data:
                    # It's a StageCoord
                    allowed_keys = StageCoord.__dataclass_fields__.keys()
                    filtered_data = {k: v for k, v in well_data.items() if k in allowed_keys}
                    # Convert list to tuple for xy if needed
                    if 'xy' in filtered_data and isinstance(filtered_data['xy'], list):
                        filtered_data['xy'] = tuple(filtered_data['xy'])
                    result[well_name] = StageCoord(**filtered_data)
                else:
                    # It's a square well
                    allowed_keys = WellSquareCoord.__dataclass_fields__.keys()
                    filtered_data = {k: v for k, v in well_data.items() if k in allowed_keys}
                    # Convert lists to tuples if needed
                    for key in ['top_left', 'bottom_right']:
                        if key in filtered_data and isinstance(filtered_data[key], list):
                            filtered_data[key] = tuple(filtered_data[key])
                    result[well_name] = WellSquareCoord(**filtered_data)
            else:
                # Not coordinate data - keep as dict
                result[well_name] = well_data
        else:
            # Already converted by decode_dataclass
            result[well_name] = well_data
    
    return result

def save_config_file(file_path: Path, data: dict[str, Any]) -> None:
    """
    Save a dictionary to a JSON file, encoding dataclass objects as needed.
    """
    with open(file_path, "w") as outfile:
        json.dump(data, outfile, default=encode_dataclass, indent=4)