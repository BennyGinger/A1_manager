from __future__ import annotations # Enable type annotation to be stored as string

from pycromanager import Core

from a1_manager.microscope_hardware.lamps.base_lamp import Lamp

class DiaLamp(Lamp):
    # Default LED label
    _led_default = {'bf':''}
    
    @property
    def LEDdefault(self) -> dict[str, str]:
        """Return the LED configuration mapping for DiaLamp."""
        return self._led_default
    
    def __init__(self, core: Core, lamp_name: str) -> None:
        super().__init__(core, lamp_name)
    
    def select_LED(self, led: str | list[str])-> None:  # type: ignore[override]
        if led != 'bf':
            raise ValueError(f"Wrong Lamp label. Must be 'bf'")
        
        self.core.set_property('DiaLamp', 'State', 1) # type: ignore[call-arg]
    
    # No real need to reset the LED for DiaLamp, just for consistency with the base class.  
    def reset_LED(self) -> None:
        # No LED selection to reset beyond setting state to 0.
        self.core.set_property('DiaLamp', 'State', 0) # type: ignore[call-arg]
    
    def validate_led_selection(self, led: str | list[str]) -> list[str]:
        if led != 'bf':
            raise ValueError("Invalid LED label for DiaLamp. Must be 'bf'.")
        return ['bf']
