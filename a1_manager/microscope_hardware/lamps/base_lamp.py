from __future__ import annotations # Enable type annotation to be stored as string
from abc import ABC, abstractmethod

from pycromanager import Core


LAPP_MAIN_BRANCH = {'pE-800': 0, 'pE-4000': 1, 'DiaLamp': None}

class Lamp(ABC):
    __slots__ = 'core', 'lamp_name', 'lapp_main_branch', '_cached_lamp_state'
    
    def __init__(self, core: Core, lamp_name: str) -> None:
        self.core = core
        self.lamp_name = lamp_name  #'pE-800', 'pE-4000', 'DiaLamp'
        
        # Set the lappMainBranch
        self.lapp_main_branch = LAPP_MAIN_BRANCH[lamp_name]
        
        # Set the core shutter
        self.core.set_property('Core', 'Shutter', lamp_name) # type: ignore[call-arg]
        
        # Set Turret1 shutter
        turret_state = 0 if lamp_name == 'DiaLamp' else 1
        self.core.set_property('Turret1Shutter', 'State', turret_state) # type: ignore[call-arg]
        
        # Set LappMainBranch1 state if needed
        if self.lapp_main_branch is not None:
            self.core.set_property('LappMainBranch1', 'State', self.lapp_main_branch) # type: ignore[call-arg]
        
        # Initialize cache for lamp state
        self._cached_lamp_state: dict = {
            'fTurret': -1,
            'fWheel': -1,
            'led': '',
            'intensity': 0.0
        }
    
    @property
    @abstractmethod
    def LEDdefault(self) -> dict[str, str]:
        """Return the LED configuration mapping for this lamp type."""
        pass
    
    def _select_filters(self, fTurret: int, fWheel: int)-> None:
        """Select filter turret and filter wheel."""
        if fTurret not in range(6):
            raise ValueError(
                f"fTurret {fTurret} is out of range."
                "Valid options: 0=BF, 1=GFP, 2=LED-Cy5-A, 3=Quad(409/493/573/652), 4=Duo(505/606), 5=Tripla(459/526/596)"
            )
        if fWheel not in range(7):
            raise ValueError(
                f"fWheel {fWheel} is out of range."
                "Valid options: 0=432/515/595/730, 1=447/60, 2=474/27, 3=544/23, 4=641/75, 5=520/28, 6=524/628"
            )
        self.core.set_property('FilterTurret1', 'State', fTurret) # type: ignore[call-arg]
        self.core.set_property('FilterWheel1', 'State', fWheel) # type: ignore[call-arg]
    
    def _select_intensity(self, led: str, intensity: float)-> None:
        """"Set the intensity of the LED lamp."""
        # For pE-800, convert 405 to 400 since it does not support 405.
        if self.lamp_name=='pE-800':
            converted_led = self._convert_405_to_400(led)
            led = converted_led if isinstance(converted_led, str) else converted_led[0]
        
        # Get the channel
        channel = self.LEDdefault.get(led)
        if channel is None:
            raise ValueError(f"Invalid LED label '{led}'. Valid options: {list(self.LEDdefault.keys())}")
        
        # Set the intensity of the given channel
        self.core.set_property(self.lamp_name, f'Intensity{channel}', str(intensity)) # type: ignore[call-arg]

    def _reset_intensity(self, led: str)-> None:
        """Reset the intensity of all channels to 0."""
        if led == '':
            return
        channel = self.LEDdefault.get(led)
        self.core.set_property(self.lamp_name, f'Intensity{channel}', 0) # type: ignore[call-arg]
    
    def set_LED_shutter(self, state: int)-> None:
        """0=close, 1=open"""
        self.core.set_property(self.lamp_name, 'Global State', state) # type: ignore[call-arg]

    def preset_channel(self, oc_dict: dict[str, int | str | float], intensity: float | None)-> None:
        """
        Set the optical configuration for the lamp.
        Args:
            oc_dict (dict): Optical configuration dictionary.
            intensity (float | None): Intensity value to set.
        """
        if intensity is not None:
            oc_dict['intensity'] = intensity
        
        # Extract values
        fTurret = int(oc_dict['fTurret'])
        fWheel = int(oc_dict['fWheel'])
        led = str(oc_dict['led'])
        intensity_val = float(oc_dict['intensity'])

        # Only update filters if they have changed
        if (self._cached_lamp_state['fTurret'] != fTurret or self._cached_lamp_state['fWheel'] != fWheel):
            self._select_filters(fTurret, fWheel)
            self._cached_lamp_state['fTurret'] = fTurret
            self._cached_lamp_state['fWheel'] = fWheel
        
        # Only update LED if it has changed
        if self._cached_lamp_state['led'] != led:
            # Switch off previous LED before changing to new one
            self.reset_LED(self._cached_lamp_state['led'])
            # self._reset_intensity(self._cached_lamp_state['led'])
            self._cached_lamp_state['intensity'] = 0.0  # Reset intensity cache since we turned it off
            # Select new LED
            self.select_LED(led)
            self._cached_lamp_state['led'] = led
        
        # Only update intensity if it has changed
        if self._cached_lamp_state['intensity'] != intensity_val:
            self._select_intensity(led, intensity_val)
            self._cached_lamp_state['intensity'] = intensity_val
    
    def clear_lamp_cache(self) -> None:
        """Clear the lamp cache to force all settings to be reapplied on next call."""
        self._cached_lamp_state: dict[str, int | str | float | None] = {
            'fTurret': -1,
            'fWheel': -1,
            'led': '',
            'intensity': 0.0}

    @staticmethod
    def _convert_405_to_400(led: str | list[str]) -> str | list[str]:
        """Convert 405 to 400 for pE-800."""
        if isinstance(led, list):
            return ['400' if item == '405' else item for item in led]
        return '400' if led == '405' else led
    
    @abstractmethod
    def select_LED(self, led: str | list[str]) -> None:
        """Select the LED lamp."""
        pass
    
    @abstractmethod
    def reset_LED(self) -> None:
        """Reset the LED lamp."""
        pass
    
    @abstractmethod
    def validate_led_selection(self, led: str | list[str]) -> list[str]:
        """Validate the LED selection."""
        pass
