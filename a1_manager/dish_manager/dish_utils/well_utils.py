from dataclasses import dataclass

from utils.class_utils import StageCoord


@dataclass
class WellBaseCoord:
    """Base class for well coordinates."""
    
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
    """Class that encapsulates the coordinates of a squared well."""
    
    top_left: tuple[float, float]
    bottom_right: tuple[float, float]

@dataclass
class WellCircleCoord(WellBaseCoord):
    """Class that encapsulates the coordinates of a circular well."""
    
    center: tuple[float, float]
    radius: float

    