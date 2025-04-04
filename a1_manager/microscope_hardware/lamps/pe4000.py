from __future__ import annotations # Enable type annotation to be stored as string

from pycromanager import Core

from microscope_hardware.lamps.base_lamp import Lamp


class pE4000(Lamp):
    # Default LED label
    LEDdefault = {
        '365':'A','385':'A','405':'A','435':'A',
        '460':'B','470':'B','490':'B','500':'B',
        '525':'C','550':'C','580':'C','595':'C',
        '635':'D','660':'D','740':'D','770':'D',
        }
    
    def __init__(self, core: Core, lamp_name: str) -> None:
        super().__init__(core, lamp_name)
    
    #TODO: Note form Raph: Is this method meant to be also called from outside the class? If not, we can make it private. Currently only called from select_LED method.
    def reset_LED(self)-> None:
        channel_lst = set([val for val in self.LEDdefault.values()])
        for channel in channel_lst:
            self.core.set_property('pE-4000', f'Selection{channel}', 0)
        self.core.set_property('DiaLamp', 'State', 0)
    
    #TODO: Note form Raph: Is this method meant to be also called from outside the class? If not, we can make it private. Currently only called from select_LED method.
    def validate_led_selection(self, led: str | list[str]) -> list[str]:
        if not isinstance(led, (str, list)):
            raise TypeError("LED channel must be a string or list of strings.")
        if isinstance(led, str):
            led = [led]
        if not all(item in self.LEDdefault for item in led):
            raise ValueError(f"Invalid LED selection. Valid options: {list(self.LEDdefault.keys())}")
        
        # Prevent selecting multiple LEDs that map to the same channel.
        channels = [self.LEDdefault[item] for item in led]
        duplicates = self._find_duplicates(channels)
        if duplicates:
            raise ValueError(
                f"Duplicate LED channel selections: {duplicates}. "
                "Only one LED per channel is allowed.")
        return led
    
    @staticmethod
    def _find_duplicates(items: list[str]) -> list[str]:
        seen = set()
        duplicates = []
        for item in items:
            if item in seen:
                duplicates.append(item)
            else:
                seen.add(item)
        return duplicates
    
    def select_LED(self, led: str | list[str]) -> None:
        self.reset_LED()
        led_list = self.validate_led_selection(led)
        for label in led_list:
            channel = self.LEDdefault[label]
            # Set both channel assignment and selection.
            self.core.set_property('pE-4000', f'Channel{channel}', label)
            self.core.set_property('pE-4000', f'Selection{channel}', 1)
