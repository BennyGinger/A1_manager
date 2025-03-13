from dataclasses import asdict

from a1_manager.utils.utility_classes import WellCircleCoord, WellSquareCoord


def encode_dataclass(obj: any) -> dict:
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
def decode_dataclass(data: dict)-> WellCircleCoord | WellSquareCoord:
    """Decode a dictionary into a dataclass object."""
    
    if "__class__" in data:
        cls_name = data.pop("__class__")
        if cls_name == "WellSquareCoord":
            return WellSquareCoord(**data)
        elif cls_name == "WellCircleCoord":
            return WellCircleCoord(**data)
    return data