from dataclasses import dataclass
from typing import Literal, overload, Any


@dataclass
class StageCoord:
    """Class to store the stage coordinates. Support dict-like access."""
    xy: tuple[float, float]
    ZDrive: float | None = None
    PFSOffset: float | None = None
    
    
    # Support dict-like access, and return the corresponding attribute with dynamic type hint
    @overload
    def __getitem__(self, key: Literal['xy']) -> tuple[float, float]: ...
    
    @overload
    def __getitem__(self, key: Literal['ZDrive']) -> float | None: ...
    
    @overload
    def __getitem__(self, key: Literal['PFSOffset']) -> float | None: ...
    
    def __getitem__(self, key: str)-> tuple[float, float] | float | None:
        return getattr(self, key)