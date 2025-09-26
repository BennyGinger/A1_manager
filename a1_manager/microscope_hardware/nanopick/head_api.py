
from __future__ import annotations # Enable type annotation to be stored as string
import logging

import requests

from a1_manager.microscope_hardware.nanopick.marZ_api import MarZ
from utils.utility_classes import StageCoord # Do I need the center position since the stage movement is handled by the Nikon class?

# Set up logging
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000"

# Volumes
FILL_VOLUME = 500
INJECT_VOLUME = 70
MIXING_VOLUME = 50
MAX_VOLUME = 600

# Movement of the head
MOVING_UP = -33000
MOVING_DOWN = 33000

class Head():
    """Class that controls the API head.
    """
    __slots__ = 'arm', '_track_volume'
    
    def __init__(self, arm: MarZ) -> None:
        self.arm = arm
        self._track_volume = 0  # in nanoliters
    
    @property
    def track_volume(self) -> float:
        return self._track_volume
    
    # TODO: Check time default value
    def set_volume(self, volume: float, time: float = 100) -> None:
        """ A volume-time pair is sent to the controller. The piezo unit will start immediately 
            to withdraw or inject the specified volume under the specified time. The volume values 
            are absolute values. If the volume is less than the previously sent item, then fluid is 
            withdrawn through the pipette. If the volume is greater than the previously sent one, fluid 
            will be injected back."""        

        #Endpoint and parameters
        endpoint = f"{BASE_URL}/setVolume"
        params = {
            "volume": volume,   # example volume in nanoliters
            "time": time    # example time in milliseconds
        }
        try:
            response = requests.put(endpoint, params=params)

            if response.status_code == 200:
                logger.debug("Success:", response.text)
            else:
                logger.error(f"Error {response.status_code}:", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("Request failed:", e)
    
    def set_LED(self, ID: int, brightness: int) -> None:
        """Set brightness level of LED """
        #Endpoint and parameters
        endpoint = f"{BASE_URL}/setLED"
        params = {
            "ID": ID,   # example volume in nanoliters
            "brightness": brightness }   # example time in milliseconds
        try:
            response = requests.put(endpoint, params=params)

            if response.status_code == 200:
                logger.debug("Success:", response.text)
            else:
                logger.error(f"Error {response.status_code}:", response.text)
        except requests.exceptions.RequestException as e:
            logger.error("Request failed:", e)

    def _update_volume(self, volume: float, state: str) -> float:
            if state == "fill":
                self._track_volume += volume
            
            if state == "inject":
                self._track_volume += volume
                
            if state == "flush":
                self._track_volume -= volume
        
    # TODO: Check flush default volume     
    def flushing(self) -> None: 
        # Get all the fluid out of the pipette       
        self.set_volume(self.track_volume)
        self.update_volume(self.track_volume, "flush")
    
    # TODO: Check filling default volume 
    def filling(self, volume: float = FILL_VOLUME) -> None:              
        # Check if the pipette is empty, if not, then flush it out
        if self.track_volume != 0:
            self.flushing()
        # Check if the filling does not cause an overflow
        if self.track_volume + volume >= MAX_VOLUME:
            logger.warning("The pipette is about to fill up! Please choose a new value between zero and %s", (self.track_volume + volume -5))
        else:
            # Move down the head to reach the liquid
            self.Arm.set_head_position(MOVING_DOWN)
                    
            # Draw the liquid into the pipette        
            self.set_volume(volume)
            self.update_volume(volume, "fill")
                    
            # Move up the head
            self.Arm.set_head_position(MOVING_UP) 
    
    # TODO: Check inject default volume 
    def injecting(self, volume: float = INJECT_VOLUME) -> None: 
        # Check if there is enough liquid to inject   
        if self.track_volume < volume:  
            logger.warning("There is not enough liquid in the pipette. Please refill it!")
        else:             
            # Move down the head to reach the liquid
            self.Arm.set_head_position(MOVING_DOWN)
                    
            # Draw the liquid into the pipette        
            self.set_volume(volume)
            self.update_volume(volume, "inject")
                    
            # Move up the head
            self.Arm.set_head_position(MOVING_UP) 
    
    # TODO: Check mixing default volume
    def mixing(self, n: int, volume: float = MIXING_VOLUME):
        # Check if the pipette is empty, if not, then flush it out
        if self.track_volume != 0:
            self.flushing()
        else:
            # Move down the head to reach the liquid
            self.Arm.set_head_position(MOVING_DOWN)
                    
            # Draw the liquid into the pipette 
            # 'n': number of mixing cycles
            for i in range(n):       
                self.set_volume(volume) # suck it up
                self.set_volume(-volume) # let it out
                    
            # Move up the head
            self.Arm.set_head_position(MOVING_UP) 
