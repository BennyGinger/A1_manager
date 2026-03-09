from __future__ import annotations # Enable type annotation to be stored as string
from abc import ABC, abstractmethod
import logging
import serial
import time
from dataclasses import dataclass
import logging

import requests

# Set up logging
logger = logging.getLogger(__name__)

class InjectionDevice(ABC):
    """ Abstract base class for injection devices. """
    
    def __init__(self) -> None:
        pass

    @abstractmethod
    def inject(self, inject_vol_ul: float, inject_time_ms: int | None = None, mixing_cycles: int = 1) -> None:
        """ Inject a specified volume using the device.
        
        Args:
            inject_vol_ul (float): Volume to inject in microliters.
            inject_time_ms (int | None): Time to inject in milliseconds. If None, volume-based injection is used.
            mixing_cycles (int): Number of mixing cycles during injection.
        """
        pass
    
    @abstractmethod
    def fill(self, fill_vol_nl: float, fill_time_ms: int | None = 100) -> None:
        """ Fill the device with a specified volume.
        
        Args:
            fill_vol_nl (float): Volume to fill in nanoliters.
            fill_time_ms (int | None): Time to fill in milliseconds. If None, volume-based filling is used.
        """
        pass
    
    @abstractmethod
    def set_led_ring(self, ring: int = 0, brightness: int | None = None) -> None:
        """ Set the LED ring state.
        
        Args:
            ring (int): Ring number (0 for off, 1 for inner, 2 for outer).
            brightness (int | None): Brightness level (if applicable).
        """
        pass
    

