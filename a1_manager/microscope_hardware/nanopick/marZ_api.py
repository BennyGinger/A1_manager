from __future__ import annotations # Enable type annotation to be stored as string
import logging
from dataclasses import dataclass, field
from time import sleep
import warnings

# Suppress pycromanager version mismatch warning
warnings.filterwarnings("ignore", message=".*Java ZMQ server and Python client.*")

from pycromanager import Core

# Set up logging
logger = logging.getLogger(__name__)

DISTANCE_TO_LIQUID = {'96well': 10_180.0}   # Set to be ~ 3000 um above the bottom of the well in 100 um volume
# DISTANCE_TO_AIR = {'96well': 9_000.0}   # Set to be ~ 2000 um above the plate 

@dataclass(slots=True)
class MarZ():
    """
    Class to control the movement of the arm (Märzhäuser controller).
    """
    core: Core
    dish: str
    _ref_position: float = field(init=False)

    def __post_init__(self):
        self._init_ref_position()
        logger.debug(f"Arm initialized at reference position: {self._ref_position}")
    
    def _init_ref_position(self) -> None:
        """
        Initialize the reference position of the arm.
        """
        # Set the speed of the Z axis
        self.core.set_property('ZAxis', 'SpeedZ [mm/s]', 25) # type: ignore
        self.core.set_property('ZAxis', 'Acceleration Z [m/s^2]', 0.05) # type: ignore
        
        # Ensure that the arm is at the top position when initialized
        # This up and down sequence ensures accurate homing
        self._set_arm_position(100000)
        self.core.wait_for_device('ZAxis') # type: ignore
        self._set_arm_position(round(self._get_arm_position-5000))
        self.core.wait_for_device('ZAxis') # type: ignore
        self._set_arm_position(100000)
        self.core.wait_for_device('ZAxis') # type: ignore
        # Set the reference position just below the top position, i.e. where the accuracy is 100%
        self._set_arm_position(round(self._get_arm_position-500))
        # Store the reference position
        self._ref_position = self._get_arm_position
    
    @property
    def _get_arm_position(self) -> float:
        """
        Get the current altitude of the head.
        """
        return self.core.get_position('ZAxis') # type: ignore
    
    def to_liquid(self) -> None:
        """
        Move to the position in the liquid safely above the cells.
        """
        return self._set_arm_position(self._ref_position - DISTANCE_TO_LIQUID[self.dish])

    def to_home(self) -> None:
        """
        Move to the safe height above the plate.
        """
        return self._set_arm_position(self._ref_position)
    
    def _set_arm_position(self, position: float) -> None:
        """
        Move the arm to the desired position.
        Args:
            position (float): The target altitude for the arm.
        """
        self.core.set_position('ZAxis', position) # type: ignore
        self.core.wait_for_device('ZAxis') # type: ignore
    
    def safe_check(self) -> None:
        """
        Check the altitude before moving to avoid at any cost of breaking the needle.
        """
        if self._get_arm_position < self._ref_position:
            logger.warning("The arm is too low, it will sent home!")
            self._set_arm_position(self._ref_position)
            
if __name__ == "__main__":
    import warnings

    # Suppress pycromanager version mismatch warning
    warnings.filterwarnings("ignore", message=".*Java ZMQ server and Python client.*")
    
    # Example usage
    arm = MarZ(core=Core(), dish='96well') # type: ignore

    print("Current head position:", arm._get_arm_position)
    sleep(5)
    arm.to_liquid()
    print("Current head position after moving to liquid:", arm._get_arm_position)
    sleep(5)
    arm.to_home()
    print("Current head position after moving to home:", arm._get_arm_position)
    
