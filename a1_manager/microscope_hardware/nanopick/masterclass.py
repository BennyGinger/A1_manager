from __future__ import annotations # Enable type annotation to be stored as string
import logging
from dataclasses import dataclass
from a1_manager.microscope_hardware.nanopick.marZ_api import MarZ

from pycromanager import Core # type: ignore



# Set up logging
logger = logging.getLogger(__name__)

# initialize arm always and create a condition for the head or the valves to initialize - so it will be a condition inside this class which will get as a parameter

class InjecterManager:
    "Class to control the injection depending on the chosen device: nanopick head or quicpick valve control."
    __slots__ = 'core', 'arm', 'attachment'
    
    def __init__(self,nanopick_dish: str, injection_device: str = None): # type: ignore
        self.core = Core()
        """
            Possible device names:
            - 'nanopick'
            - 'quickpick'
        """
        self.arm = MarZ(self.core, nanopick_dish) # type: ignore
        if injection_device == "nanopick":
            from a1_manager.microscope_hardware.nanopick.head_api import Head
            self.attachment = Head(self.arm)
        if injection_device == "quickpick":
            from a1_manager.microscope_hardware.nanopick.valves import PICController
            self.attachment =  PICController(port='COM10', timeout=1.0)
            
# Example usage
if __name__ == "__main__":
    import time
    from a1_manager import A1Manager
    a1_manager = A1Manager(objective= '20x', nanopick_dish='96well', lamp_name='pE-800', injection_device='quickpick')
    controller =a1_manager.injection.attachment

    print("Testing connection:", controller.test_connection()) # type: ignore
    #print("Toggle LED2:", controller.toggle_led2())
    print("Set switch 1 ON:", controller.set_switch(1, '+')) # type: ignore
    print("Query all outputs:", controller.query_all_outputs()) # type: ignore
    print("Set Valve1 time 100 ms:", controller.set_valve_time(1, 100)) # type: ignore
    print("Set delay 200 ms:", controller.set_delay(200)) # type: ignore

    print("Set ring 1:", controller.set_led_ring(1)) # type: ignore
    time.sleep(1)
    print("Set ring 2:", controller.set_led_ring(2)) # type: ignore
    time.sleep(1)
    print("Turn off rings:", controller.set_led_ring(0)) # type: ignore
    controller.set_valve_time(1, 400) # type: ignore
    controller.set_valve_time(2, 500) # type: ignore
    controller.set_delay(300) # type: ignore
    # print("Open Valve1:", controller.open_valve(1))
    # print("Open Valve2:", controller.open_valve(2))
    print("Open both valves (1 then 2):", controller.open_valves_sequence('K')) # type: ignore
    time.sleep(1)  # Wait a bit before the next command
    # print("Open both valves (2 then 1):", controller.open_valves_sequence('L'))
    # print("Testing connection:", controller.test_connection())
    controller.close() # type: ignore

     
     
     
     
     

            