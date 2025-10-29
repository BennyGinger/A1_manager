from __future__ import annotations # Enable type annotation to be stored as string
import logging
from dataclasses import dataclass, field
from time import sleep

from pycromanager import Core

# Set up logging
logger = logging.getLogger(__name__)

DISTANCE_TO_LIQUID = {'96well': 15_000.0}   # Set to be 2000 um above the bottom of the well.
DISTANCE_TO_AIR = {'96well': 5_000.0}   # Set to be 1000 um above the plate.


@dataclass(slots=True)
class MarZ:
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
        # Ensure that the arm is at the top position when initialized
        # This up and down sequence ensures accurate homing
        self._set_arm_position(100000)
        self._set_arm_position(round(self._get_arm_position-5000))
        self._set_arm_position(100000)
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

    def to_air(self) -> None:
        """
        Move to the safe height above the plate.
        """
        return self._set_arm_position(self._ref_position - DISTANCE_TO_AIR[self.dish])
    
    def _set_arm_position(self, position: float) -> None:
        """
        Move the arm to the desired position.
        Args:
            position (float): The target altitude for the arm.
        """
        self.core.set_position('ZAxis', position) # type: ignore
        self.core.wait_for_device('ZAxis') # type: ignore
    
                
    
 
if __name__ == "__main__":
    import warnings

    # Suppress pycromanager version mismatch warning
    warnings.filterwarnings("ignore", message=".*Java ZMQ server and Python client.*")
    
    # Example usage
    arm = MarZ(core=Core(), dish='96well') # type: ignore

    print("Current head position:", arm._get_arm_position)
    arm.to_air()
    print("Current head position after moving to air:", arm._get_arm_position)
    # sleep(5)
    # arm.to_liquid()
    # print("Current head position after moving to liquid:", arm._get_arm_position)
    # sleep(5)
    # arm._set_arm_position(arm._ref_position)
    # print("Current head position after going home:", arm._get_arm_position)