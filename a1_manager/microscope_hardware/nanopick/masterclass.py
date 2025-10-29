from __future__ import annotations # Enable type annotation to be stored as string
import logging
from dataclasses import dataclass
from a1_manager.microscope_hardware.nanopick.marZ_api import MarZ

from pycromanager import Core # type: ignore



# Set up logging
logger = logging.getLogger(__name__)

# initialize arm always and create a condition for the head or the valves to initialize - so it will be a condition inside this class which will get as a parameter
# Question: what functions should I do in the main a1 manager? - let's take a look at the lamp functions

class InjecterManager:
    "Class to control the injection depending on the chosen device: nanopick head or quicpick valve control."
    __slots__ = 'core', 'arm', 'attachment'
    
    def __init__(self, injection_device: str = None):
        self.core = Core()
        """
            Possible device names:
            - 'nanopick'
            - 'quickpick'
        """
        self.arm = MarZ(self.core)
        if injection_device == "nanopick":
            from a1_manager.microscope_hardware.nanopick.head_api import Head
            self.attachment = Head(self.arm)
        if injection_device == "quickpick":
            from a1_manager.microscope_hardware.nanopick.valves import PICController
            self.attachment =  PICController(port='COM10', timeout=1.0)
     
     
     
     
     

            
            
        
            
        