from __future__ import annotations # Enable type annotation to be stored as string

from pycromanager import Core

from microscope_hardware.lamps.base_lamp import Lamp

class DiaLamp(Lamp):
    # Default LED label
    LEDdefault = {'bf':''}
    
    def __init__(self, core: Core, lamp_name: str) -> None:
        super().__init__(core, lamp_name)
    
    def select_LED(self, led: str)-> None:
        if led != 'bf':
            raise ValueError(f"Wrong Lamp label. Must be 'bf'")
        
        self.core.set_property('DiaLamp', 'State', 1)
    
    #TODO: Note form Raph: Is this method meant to be also called from the user? If not, we can make it private.
    # No real need to reset the LED for DiaLamp, just for consistency with the base class.  
    def reset_LED(self) -> None:
        # No LED selection to reset beyond setting state to 0.
        self.core.set_property('DiaLamp', 'State', 0)
    
    #TODO: Note form Raph: Is this method meant to be also called from the user? If not, we can make it private.
    def validate_led_selection(self, led: str | list[str]) -> list[str]:
        if led != 'bf':
            raise ValueError("Invalid LED label for DiaLamp. Must be 'bf'.")
        return ['bf']
