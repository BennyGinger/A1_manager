from __future__ import annotations # Enable type annotation to be stored as string

from pycromanager import Core

from microscope_hardware.lamps.base_lamp import Lamp


class pE800(Lamp):
    # Default LED label
    LEDdefault = {'400':'A','435':'B','470':'C','500':'D','740':'E','635':'F','580':'G','550':'H'}
    
    def __init__(self, core: Core, lamp_name: str) -> None:
        super().__init__(core, lamp_name)
    
    def reset_LED(self)-> None:
        for channel in self.LEDdefault.values():
            self.core.set_property('pE-800', f'Selection{channel}', 0)
        self.core.set_property('DiaLamp', 'State', 0)
    
    def validate_led_selection(self, led: str | list[str]) -> list[str]:
        if not isinstance(led, (str, list)):
            raise TypeError("LED channel must be a string or list of strings.")
        if isinstance(led, str):
            led = [led]
        led = self.convert_405_to_400(led)
        if not all(item in self.LEDdefault for item in led):
            raise ValueError(f"Invalid LED selection. Valid options: {list(self.LEDdefault.keys())}")
        return led
    
    def select_LED(self, led: str | list[str]) -> None:
        self.reset_LED()
        led_list = self.validate_led_selection(led)
        for label in led_list:
            channel = self.LEDdefault[label]
            self.core.set_property('pE-800', f'Selection{channel}', 1)
