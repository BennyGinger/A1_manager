from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass, replace
from typing import Any, Literal, overload


@dataclass
class StageCoord:
    """Class to store the stage coordinates. Support dict-like access.
    
    Attrbuttes:
        xy: Tuple[float, float]: The x and y coordinates of the stage.
        ZDrive: float: The ZDrive position.
        PFSOffset: float: The PFS offset."""
    xy: tuple[float | None, float | None] = (None, None)
    ZDrive: float | None = None
    PFSOffset: float | None = None
    
    
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

    def get(self, key: str, default=None) -> tuple[float, float] | float | None:
        """Mimic dict.get(): Return the value for key if key is in the object, else default."""
        return getattr(self, key, default)
    
    def copy(self) -> "StageCoord":
        """Return a shallow copy of the object."""
        return replace(self)
    
@dataclass
class WellBaseCoord:
    """
    Base class to store the coordinates of a well. Support dict-like access.
    
    Attributes:
        - ZDrive: float: The ZDrive position.
        - PFSOffset: float: The PFS offset.
    """
    
    ZDrive: float | None = None
    PFSOffset: float | None = None
    
    def __getitem__(self, key: str):
        return getattr(self, key)
    
    def __setitem__(self, key: str, value: Any | None):
        setattr(self, key, value)
    
    def _items(self):
        return self.__dict__.items()
    
    def get_template_point_coord(self) -> StageCoord:
        """Return a template StageCoord object (i.e. without any xy coord) with the focus values of the well."""
        temp_point = StageCoord()
        for k,v in self._items():
            if hasattr(temp_point, k):
                setattr(temp_point, k, v)
        return temp_point

@dataclass
class WellSquareCoord(WellBaseCoord):
    """
    Class that encapsulates the coordinates of a squared well.
    
    Attributes:
        - ZDrive: float: The ZDrive position.
        - PFSOffset: float: The PFS offset.
        - top_left: Tuple[float, float]: The coordinates of the top left corner.
        - bottom_right: Tuple[float, float]: The coordinates of the bottom right corner.
    """
    
    top_left: tuple[float, float] | None = None
    bottom_right: tuple[float, float] | None = None
    
    @property
    def center(self) -> tuple[float, float] | None:
        if self.top_left is not None and self.bottom_right is not None:
            x = (self.top_left[0] + self.bottom_right[0]) / 2
            y = (self.top_left[1] + self.bottom_right[1]) / 2
            return (x, y)
        return None

@dataclass
class WellCircleCoord(WellBaseCoord):
    """
    Class that encapsulates the coordinates of a circular well.
    
    Attributes:
        - ZDrive: float: The ZDrive position.
        - PFSOffset: float: The PFS offset.
        - center: Tuple[float, float]: The coordinates of the center of the circle.
        - radius: float: The radius of the circle.
    """
    
    center: tuple[float, float] | None = None
    radius: float | None = None
    