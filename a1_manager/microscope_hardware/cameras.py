from __future__ import annotations # Enable type annotation to be stored as string

from pycromanager import Core


class AndorCamera:
    __slots__ = ('core','binning','exposure_ms')
    
    def __init__(self, core: Core, binning: int=2, exposure_ms: float=100) -> None:
        self.core = core
        
        # Set the light path to camera
        self.core.set_property('LightPath','State',1)
        
        # Set the camera properties
        self.set_camera_binning(binning)
        self.set_camera_exposure(exposure_ms)
    
    #TODO: Note form Raph: Is this method meant to be also called from the user? If not, we can make it private.
    def set_camera_binning(self, binning: int)-> None:
        """Set the camera binning."""
        self.core.set_property('Andor sCMOS Camera','Binning',f"{binning}x{binning}")
        self.binning = binning

    def set_camera_exposure(self, exposure_ms: float)-> None:
        """Set the camera exposure time."""
        self.core.set_property('Andor sCMOS Camera', 'Exposure', exposure_ms)
        self.exposure_ms = exposure_ms
    