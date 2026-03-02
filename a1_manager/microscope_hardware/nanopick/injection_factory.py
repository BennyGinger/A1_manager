from __future__ import annotations # Enable type annotation to be stored as string
import logging

from a1_manager import StageCoord

# Set up logging
logger = logging.getLogger(__name__)

class Injection():
    """ 
    Class to control the injection depending on the chosen device: nanopick head or quickpick valve control.
    Args:
        - arm
        - injection_device
        - a1_manager
    """
    
    __slots__ =  'arm', 'injection_device', 'a1_manager'
    
    def __init__(self, arm, injection_device, a1_manager): # type: ignore
        
        self.arm = arm
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

    
    

    
