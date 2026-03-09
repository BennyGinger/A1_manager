from __future__ import annotations # Enable type annotation to be stored as string
import logging

from a1_manager.microscope_hardware.nanopick.devices.marZ import MarZ
from a1_manager.microscope_hardware.nanopick.devices.injection_device import InjectionDevice
from a1_manager import StageCoord
from pycromanager import Core

# Set up logging
logger = logging.getLogger(__name__)

class Injection():
    """ 
    Class to control the injection depending on the chosen device: nanopick head or quickpick valve control.
    Args:
        - injection_volume(float): injected volume in microliters
        - injection_time(int): injection time in milliseconds
        - nanopick_dish(str): name of the used dish (e.g.: "96-well")
    """
    
    __slots__ =  'arm', 'injection_device',  'dish_name'
    
    def __init__(self,  injection_device: str, dish_name: str, needle_size: int | None = None, pressure: float | None = None): # type: ignore
        self.arm = MarZ(core = Core(), dish_name) # type: ignore    
        self.dish_name = dish_name
        
        if injection_device == "nanopick":
            from a1_manager.microscope_hardware.nanopick.devices.head import Head  
            self.injection_device = Head()
            
        if injection_device == "quickpick":
            if needle_size == None or pressure == None:
                    logger.error("Needle size and pressure value is needed for using the valve system.")
            else:
                    from a1_manager.microscope_hardware.nanopick.devices.valve import PICController
                    self.injection_device = PICController(needle_size = needle_size, pressure=pressure)
                
        # Fallback for unsupported strings
        raise ValueError(f"Unsupported injection device: {injection_device}")
    
    def position_converter(self, position: tuple[float, float]) -> StageCoord:
        """ 
        Convert position from tuple to StageCoord.
        """
        return StageCoord(position)
    
    def _ul_to_nl_converter(self, volume_ul: float) -> float:
        """
        Convert volume from microliters to nanoliters.
        """
        return volume_ul*1000
    
    def arm_to_home(self)->None:
        """
        Move to the safe height above the plate.
        """
        return self.arm.to_home()
    
    def arm_to_liquid(self)->None:
        """
        Move to the position in the liquid safely above the cells.
        """
        return self.arm.to_liquid()
        
    def get_arm_position(self)-> float:
        """
        Get the current altitude of the head.
        """
        return self.arm._get_arm_position
        
    def inject(self,  inject_vol_ul: float, injection_time_ms: float | None = None, mixing_cycles: int = 1) -> None:
        """ 
        Injection function to control the injection depending on the chosen device: nanopick head or quickpick valve control.

        Args:
        - injection_volume_ul(float): injected volume in microliters
        - injection_time_ms(float): injection time in milliseconds (only needed for nanopick head control)
        """
        if self.injection_device == "nanopick":
                injection_volume = self._ul_to_nl_converter(inject_vol_ul)
        else:
                injection_volume = inject_vol_ul
                
        self.arm_to_home()
        self.injection_device.inject(injection_volume, injection_time_ms)    
        self.arm_to_liquid()
        self.arm_to_home()

    

    