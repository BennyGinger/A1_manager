from __future__ import annotations # Enable type annotation to be stored as string
import logging
from dataclasses import dataclass
import logging

from a1_manager.microscope_hardware.nanopick.devices.injection_device import InjectionDevice

import requests

# Set up logging
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:5000/api"  # Base URL for the API

# Volumes
MAX_VOLUME = 500 # in nanoliters
MIN_VOLUME = 10  # in nanoliters


@dataclass(slots=True)
class Head(InjectionDevice):
    """
    Class that controls the API head.
    """

    _track_volume: float = MAX_VOLUME  # in nanoliters

    def __post_init__(self):
        self.switch_LED_off()
    
    @property
    def get_track_volume(self) -> float:
        return self._track_volume
    
    def _set_volume(self, volume_nl: float, time_ms: float | None = None) -> None:
        """
        A volume-time pair is sent to the controller. The piezo unit will start immediately to withdraw or inject the specified volume under the specified time. 
        The volume values are absolute values. If the volume is less than the previously sent item, then fluid is withdrawn 
        through the pipette. 
        If the volume is greater than the previously sent one, fluid will be injected back.
        
        Args:
            volume_nl (float): Volume in nanoliters 
            time_ms (float): Time in milliseconds (default: 100 ms)
        """

        # Endpoint and parameters
        endpoint = f"{BASE_URL}/setVolume?volume={volume_nl}&time={time_ms}"
        try:
            response = requests.put(endpoint)
            if response.status_code == 200:
                logger.debug(f"Success: {response.text}")
            else:
                logger.error(f"Error {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")

            
    def set_led_ring(self, ring: int, brightness: int | None = None) -> None:
        """
        Set brightness level of LED 
        
        Args:
            ring (int): LED ID (1-2)
            brightness (int): Brightness level (0-100)
        """
        if brightness == None:
            logger.error("You forgot to add a value for brightness between 0 and 100.")
        else:
            # Endpoint and parameters
            endpoint = f"{BASE_URL}/setLED/{ring}?brightness={brightness}"
            try:
                response = requests.put(endpoint)
                if response.status_code == 200:
                    logger.debug(f"Success: {response.text}")
                else:
                    logger.error(f"Error {response.status_code}: {response.text}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")

    def fill(self, fill_vol_nl: float, fill_time_ms : float | None = 100) -> None:
        
        fill_vol_nl = abs(fill_vol_nl)  # Ensure volume is positive
        max_filling_volume = MAX_VOLUME - self.get_track_volume
        
        if fill_vol_nl > max_filling_volume:
            vol_to_fill = max_filling_volume
            logger.warning(f"The volume to fill exceeds the maximum volume of the pipette! It will be set to {vol_to_fill} nanoliters.")
        else:
            vol_to_fill = fill_vol_nl

        # Draw the liquid into the pipette
        self._set_volume(self.get_track_volume - vol_to_fill, fill_time_ms)
        self._track_volume += vol_to_fill

    def inject(self, inject_vol_ul: float, inject_time_ms: float | None = None, mixing_cycles: int = 1) -> None:
                
        inject_vol_nl = abs(inject_vol_ul)  # Ensure volume is positive. 
        max_injection_volume = self.get_track_volume - MIN_VOLUME
        
        if inject_vol_nl > max_injection_volume:
            vol_to_inject = max_injection_volume
            logger.warning(f"The volume to inject exceeds the current volume in the pipette! It will be set to {max_injection_volume} nanoliters (i.e. current volume - minimum volume).")
        else:
            vol_to_inject = inject_vol_nl
            
        # Draw the liquid into the pipette
        self._set_volume(self.get_track_volume + vol_to_inject, inject_time_ms)
        self._mixing(mixing_cycles, vol_to_inject)
        self._track_volume -= vol_to_inject

    def _mixing(self, mixing_cycles: int = 1, vol_to_mix: float = 0, mixing_time_ms: float = 20) -> None:
        """
        Mix the liquid in the pipette by sucking it up and letting it out multiple times.
        Args:
            mixing_cycles(int): number of mixing cycles (default: 1 - meaning there is no mixing)
            mixing_time_ms(float): time for each mixing cycle in milliseconds (default: 20 ms)
            vol_to_mix(float): volume to inject in nanoliters
        """
        
        if mixing_cycles > 1:
            for _ in range(mixing_cycles):
                self._set_volume(self.get_track_volume - vol_to_mix, mixing_time_ms)  # suck it up
                self._set_volume(self.get_track_volume + vol_to_mix, mixing_time_ms)  # let it out
        else:
            pass
