from dataclasses import dataclass


@dataclass
class WellSquare:
    """Class that encapsulates the coordinates of a squared well."""
    
    top_left: tuple[float, float]
    bottom_right: tuple[float, float]
    ZDrive: float | None = None
    PFSOffset: float | None = None

@dataclass
class WellCircle:
    """Class that encapsulates the coordinates of a circular well."""
    
    center: tuple[float, float]
    radius: float
    ZDrive: float | None = None
    PFSOffset: float | None = None
