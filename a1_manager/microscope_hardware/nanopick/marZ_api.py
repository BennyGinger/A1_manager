from __future__ import annotations # Enable type annotation to be stored as string
import logging
from dataclasses import dataclass

from pycromanager import Core

# Set up logging
logger = logging.getLogger(__name__)

MAX_HEIGHT = 7000
MIN_HEIGHT = -7000

SAFE_HEIGHT = 3500 # The stage controller has to wait until the head reaches this altitude - will be used 
@dataclass(slots=True)
class MarZ:
    """
    Class to control the movement of the arm (Märzhäuser controller).
    """
    core: Core
    destination: float

    @property
    def get_arm_position(self)->float:
        """
        Get the current altitude of the head.
        """
        return self.core.get_position('ZAxis') # type: ignore
        
    def set_arm_position(self, destination: float)->None:
        """
        Move the head to the desired position.
        Args:
            destination (float): The target altitude for the head movement (in range -7000 to 7000, arbitrary units).
        """
        if destination > MIN_HEIGHT and destination < MAX_HEIGHT:
            self.core.set_position('ZAxis', destination) # type: ignore
            self._safety_waiting()
        else:
            logger.warning("The destination is out of range! Please choose a value between %s and %s", MIN_HEIGHT, MAX_HEIGHT)
        
    def _safety_waiting(self):
        """
        Wait until the head reaches a safe height.
        """
        while True:
            height = self.get_arm_position
            if height >= SAFE_HEIGHT:
                break

