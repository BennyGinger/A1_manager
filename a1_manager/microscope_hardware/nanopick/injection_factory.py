from __future__ import annotations # Enable type annotation to be stored as string
import logging

from a1_manager.microscope_hardware.nanopick.devices.marZ import MarZ
from a1_manager.microscope_hardware.nanopick.devices.injection_device import InjectionDevice
from a1_manager import StageCoord

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
    
    __slots__ =  'arm', 'injection_time_ms', 'injection_volume_ul', 'dish_name'
    
    def __init__(self,  ): # type: ignore
        
        self.arm = MarZ(self.a1_manager.core, dish_name) # type: ignore
        self.injection_device = injection_device
        self.a1_manager = a1_manager
    
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
        
    def get_injection_device(self, injection_device: str, needle_size: int | None = None, pressure: float | None = None) -> InjectionDevice:
        """ 
        Initialize the injection device. 

        Args:
            - injection_device(str): possible device names -> 'nanopick', 'quickpick'
            - needle_size(int): for valves, possible values -> 30, 50, 70 um
            - pressure(float): for valves, possible values -> [0,6] bar - for the 50 um needle size: 0.2, 0.3, 0.4 bar
        """
        if injection_device == "nanopick":
            from a1_manager.microscope_hardware.nanopick.devices.injection_device import Head  
            return Head()
            
        if injection_device == "quickpick":
            if needle_size == None or pressure == None:
                    logger.error("Needle size and pressure value is needed for using the valve system.")
            else:
                    from a1_manager.microscope_hardware.nanopick.devices.injection_device import PICController
                    return PICController(needle_size = needle_size, pressure=pressure, test_mode= True)
                
        # Fallback for unsupported strings
        raise ValueError(f"Unsupported injection device: {injection_device}")
    
    

    
