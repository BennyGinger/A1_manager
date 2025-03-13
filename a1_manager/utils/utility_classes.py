from dataclasses import dataclass, field, replace
from typing import Literal, overload


@dataclass
class StageCoord:
    """Class to store the stage coordinates. Support dict-like access.
    
    Attrbuttes:
        xy: Tuple[float, float]: The x and y coordinates of the stage.
        ZDrive: float: The ZDrive position.
        PFSOffset: float: The PFS offset."""
    xy: tuple[float, float] = (None, None)
    ZDrive: float = None
    PFSOffset: float = None
    
    
    # Support dict-like access, and return the corresponding attribute with dynamic type hint
    @overload
    def __getitem__(self, key: Literal['xy']) -> tuple[float, float]:
        pass
    
    @overload
    def __getitem__(self, key: Literal['ZDrive']) -> float:
        pass
    
    @overload
    def __getitem__(self, key: Literal['PFSOffset']) -> float:
        pass
    
    def __getitem__(self, key: str)-> tuple[float, float] | float:
        return getattr(self, key)
    
    def copy(self) -> "StageCoord":
        """Return a shallow copy of the object."""
        return replace(self)
    
@dataclass
class WellBaseCoord:
    """Base class for well coordinates.
    
    Attributes:
        ZDrive: float: The ZDrive position.
        PFSOffset: float: The PFS offset."""
    
    ZDrive: float | None = None
    PFSOffset: float | None = None
    
    def __get_item__(self, key: str):
        return getattr(self, key)
    
    def items(self):
        return self.__dict__.items()
    
    def get_template_point_coord(self) -> StageCoord:
        temp_point = StageCoord()
        for k,v in self.items():
            if hasattr(temp_point, k):
                setattr(temp_point, k, v)
        return temp_point

@dataclass
class WellSquareCoord(WellBaseCoord):
    """Class that encapsulates the coordinates of a squared well.
    
    Attributes:
        ZDrive: float: The ZDrive position.
        PFSOffset: float: The PFS offset.
        top_left: Tuple[float, float]: The coordinates of the top left corner.
        bottom_right: Tuple[float, float]: The coordinates of the bottom right corner."""
    
    top_left: tuple[float, float] = None
    bottom_right: tuple[float, float] = None

@dataclass
class WellCircleCoord(WellBaseCoord):
    """Class that encapsulates the coordinates of a circular well.
    
    Attributes:
        ZDrive: float: The ZDrive position.
        PFSOffset: float: The PFS offset.
        center: Tuple[float, float]: The coordinates of the center of the circle.
        radius: float: The radius of the circle."""
    
    center: tuple[float, float] = None
    radius: float = None