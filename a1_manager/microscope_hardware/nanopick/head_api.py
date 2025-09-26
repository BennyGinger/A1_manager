from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass
import logging

import requests

from a1_manager.microscope_hardware.nanopick.marZ_api import MarZ
from utils.utility_classes import StageCoord # Do I need the center position since the stage movement is handled by the Nikon class? No I don't think so, since this will be handled by the higher library (e.g. gem-screening). Once you see that message, please remove the import

# Set up logging
logger = logging.getLogger(__name__)

# TODO: Check default value
BASE_URL = "http://localhost:5000"

# Volumes
MIXING_VOLUME = 50 # in nanoliters
MIXING_TIME = 20 # in milliseconds
MAX_VOLUME = 600 # in nanoliters

# Movement of the head
MOVING_UP = -33000
MOVING_DOWN = 33000


# NOTE: For now I removed some methods, like flushing, we need to experiment with the API more before doing anything.
@dataclass(slots=True)
class Head():
    """
    Class that controls the API head.
    """
    arm: MarZ
    _track_volume: float = 0  # in nanoliters

    @property
    def track_volume(self) -> float:
        return self._track_volume
    
    def _set_volume(self, volume: float, time: float = 100) -> None:
        """
        A volume-time pair is sent to the controller. The piezo unit will start immediately to withdraw or inject the specified volume under the specified time. The volume values are absolute values. If the volume is less than the previously sent item, then fluid is withdrawn through the pipette. If the volume is greater than the previously sent one, fluid will be injected back.
        
        Args:
            volume (float): Volume in nanoliters (positive value to inject, negative value to withdraw)
            time (float): Time in milliseconds (default: 100 ms)
        """

        # Endpoint and parameters
        endpoint = f"{BASE_URL}/setVolume"
        params = {"volume": volume,   # example volume in nanoliters
                    "time": time}    # example time in milliseconds
        try:
            response = requests.put(endpoint, params=params)
            if response.status_code == 200:
                logger.debug(f"Success: {response.text}")
            else:
                logger.error(f"Error {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
    
    def set_LED(self, ID: int, brightness: int) -> None:
        """
        Set brightness level of LED 
        
        Args:
            ID (int): LED ID (1-2)
            brightness (int): Brightness level (0-100)
        """
        # Endpoint and parameters
        endpoint = f"{BASE_URL}/setLED"
        params = {"ID": ID,   # example volume in nanoliters
                "brightness": brightness}   # example time in milliseconds
        try:
            response = requests.put(endpoint, params=params)

            if response.status_code == 200:
                logger.debug(f"Success: {response.text}")
            else:
                logger.error(f"Error {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")

    # FIXME: If you have time, can you check the volume handleing by the api, because I think -vol is sucking up and +vol is pushing out, but I am not 100% sure. This needs to be then changed accordingly in the code (i.e. in the injecting and filling function)
    def filling(self, volume: float, time: float = 100) -> None:
        """
        Fill the pipette with a specified volume of liquid. If the requested volume exceeds the maximum capacity of the pipette, it will be capped at MAX_VOLUME.
        """
        if volume + self.track_volume >= MAX_VOLUME:
            vol_to_fill = MAX_VOLUME - self.track_volume
            logger.warning(f"The volume to fill exceeds the maximum volume of the pipette! It will be set to {MAX_VOLUME} nanoliters (i.e. maximum).")
        else:
            vol_to_fill = volume

        # Move down the head to reach the liquid
        self.arm.set_arm_position(MOVING_DOWN)

        # Draw the liquid into the pipette
        self._set_volume(vol_to_fill, time)
        self._track_volume += vol_to_fill

        # Move up the head
        self.arm.set_arm_position(MOVING_UP)

    def injecting(self, volume: float, time: float = 100, mixing_cycles: int = 3) -> None:
        """
        Inject a specified volume of liquid from the pipette. If the requested volume exceeds the current volume in the pipette, it will be capped at the current volume.
        """
        if volume > self.track_volume:
            logger.warning(f"The volume to inject exceeds the current volume in the pipette! It will be set to {self.track_volume} nanoliters (i.e. current volume).")
            vol_to_inject = self.track_volume
        else:
            vol_to_inject = volume   
        
        # Move down the head to reach the liquid
        self.arm.set_arm_position(MOVING_DOWN)
        
        # Draw the liquid into the pipette
        self._set_volume(vol_to_inject, time)
        self._mixing(mixing_cycles)
        self._track_volume -= vol_to_inject

        # Move up the head
        self.arm.set_arm_position(MOVING_UP)

    def _mixing(self, n: int):
        """
        Mix the liquid in the pipette by sucking it up and letting it out multiple times.
        """
        for _ in range(n):
            self._set_volume(MIXING_VOLUME, MIXING_TIME)  # suck it up
            self._set_volume(-MIXING_VOLUME, MIXING_TIME)  # let it out
