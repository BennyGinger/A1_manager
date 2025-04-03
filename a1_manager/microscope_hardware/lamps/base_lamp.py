from __future__ import annotations # Enable type annotation to be stored as string

from pycromanager import Core


LAPP_MAIN_BRANCH = {'pE-800': 0, 'pE-4000': 1, 'DiaLamp': None}

class Lamp:
    __slots__ = 'core', 'lamp_name', 'lapp_main_branch'
    
    def __init__(self, core: Core, lamp_name: str) -> None:
        self.core = core
        self.lamp_name = lamp_name  #'pE-800', 'pE-4000', 'DiaLamp'
        
        # Set the lappMainBranch
        self.lapp_main_branch = LAPP_MAIN_BRANCH[lamp_name]
        
        # Set the core shutter
        self.core.set_property('Core', 'Shutter', lamp_name)
        
        # Set Turret1 shutter
        turret_state = 0 if lamp_name == 'DiaLamp' else 1
        self.core.set_property('Turret1Shutter', 'State', turret_state)
    
    def select_filters(self, fTurret: int, fWheel: int)-> None:
        if fTurret not in range(6):
            raise ValueError(
                f"fTurret {fTurret} is out of range. "
                "Valid options: 0=BF, 1=GFP, 2=LED-Cy5-A, 3=Quad(409/493/573/652), 4=Duo(505/606), 5=Tripla(459/526/596)"
            )
        if fWheel not in range(7):
            raise ValueError(
                f"fWheel {fWheel} is out of range. "
                "Valid options: 0=432/515/595/730, 1=447/60, 2=474/27, 3=544/23, 4=641/75, 5=520/28, 6=524/628"
            )
        self.core.set_property('FilterTurret1', 'State', fTurret)
        self.core.set_property('FilterWheel1', 'State', fWheel)
        
    def select_intensity(self, led: str, intensity: float)-> None:
        self.reset_intensity()
        
        # For pE-800, convert 405 to 400 since it does not support 405.
        if self.lamp_name=='pE-800':
            led = self.convert_405_to_400(led)
        
        # Get the channel
        channel = self.LEDdefault.get(led)
        if channel is None:
            raise ValueError(f"Invalid LED label '{led}'. Valid options: {list(self.LEDdefault.keys())}")
        
        # Set the intensity of the given channel
        self.core.set_property(self.lamp_name, f'Intensity{channel}', str(intensity))

    def reset_intensity(self)-> None: 
        for channel in self.LEDdefault.values():
            self.core.set_property(self.lamp_name, f'Intensity{channel}', 0)
    
    def set_LED_shutter(self, state: int)-> None:
        """0=close, 1=open"""
        self.core.set_property(self.lamp_name, 'Global State', state)
                
    def preset_channel(self, oc_dict: dict, intensity: float | None)-> None:
        if intensity is not None:
            oc_dict['intensity'] = intensity
        
        # Apply the optical configuration
        self.select_filters(oc_dict['fTurret'], oc_dict['fWheel'])
        self.select_LED(oc_dict['led'])
        self.select_intensity(oc_dict['led'], oc_dict['intensity'])
    
    @staticmethod
    def convert_405_to_400(led: str | list[str]) -> str | list[str]:
        if isinstance(led, list):
            return ['400' if item == '405' else item for item in led]
        return '400' if led == '405' else led

    # LED handling is lamp specific – subclasses must implement these.
    def select_LED(self, led: str | list[str]) -> None:
        raise NotImplementedError("Subclasses must implement select_LED.")
    
    def reset_LED(self) -> None:
        raise NotImplementedError("Subclasses must implement reset_LED.")
    
    def validate_led_selection(self, led: str | list[str]) -> list[str]:
        raise NotImplementedError("Subclasses must implement validate_led_selection.")