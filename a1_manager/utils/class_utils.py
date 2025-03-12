from dataclasses import dataclass, replace
from typing import Literal, overload


@dataclass
class StageCoord:
    """Class to store the stage coordinates. Support dict-like access."""
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