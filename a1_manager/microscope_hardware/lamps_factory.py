from __future__ import annotations # Enable type annotation to be stored as string

from pycromanager import Core

from a1_manager.microscope_hardware.lamps.base_lamp import Lamp


def get_lamp(core: Core, lamp_name: str) -> Lamp:
    """
    Factory function to create a lamp object based on the lamp name.
    Pass the core instance and lamp name to the appropriate lamp class.
    Possible lamp names:
    - 'pE-800'
    - 'pE-4000'
    - 'DiaLamp'
    """
    if lamp_name == 'pE-800':
        from microscope_hardware.lamps.pe800 import pE800
        return pE800(core, lamp_name)
    elif lamp_name == 'pE-4000':
        from microscope_hardware.lamps.pe4000 import pE4000
        return pE4000(core, lamp_name)
    elif lamp_name == 'DiaLamp':
        from microscope_hardware.lamps.dia_lamp import DiaLamp
        return DiaLamp(core, lamp_name)
    else:
        raise ValueError("Invalid lamp name. Must be one of 'pE-800', 'pE-4000', or 'DiaLamp'.")
