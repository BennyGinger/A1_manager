from __future__ import annotations # Enable type annotation to be stored as string
import logging

from a1_manager.microscope_hardware.nanopick.devices.injection_protocol import PickDevice


# Set up logging
logger = logging.getLogger(__name__)


def get_pick_device(injection_device: str, needle_size: int | None = None, pressure: float | None = None) -> PickDevice:
    """
    Factory function to create an injection device instance based on the specified type.
    Args:
    - injection_device (str): Type of injection device ("nanopick" or "quickpick").
    - needle_size (int | None): Needle size for quickpick valve control (required if injection_device is "quickpick").
    - pressure (float | None): Pressure value for quickpick valve control (required if injection_device is "quickpick").
    Returns:
    - InjectionDevice: An instance of the specified injection device.
    Raises:
    - ValueError: If an invalid injection device type is provided or if required parameters for quickpick are missing.
    """
    
    if injection_device == "nanopick":
        from a1_manager.microscope_hardware.nanopick.devices.head import Head  
        return Head()
    elif injection_device == "quickpick":
        from a1_manager.microscope_hardware.nanopick.devices.valve import PICController
        if needle_size is None or pressure is None:
            logger.error("Needle size and pressure value is needed for using the valve system.")
            raise ValueError("Needle size and pressure value is needed for using the valve system.")
        
        return PICController(needle_size = needle_size, pressure=pressure)
    else:
        logger.error(f"Invalid injection device: {injection_device}. Choose 'nanopick' or 'quickpick'.")
        raise ValueError(f"Invalid injection device: {injection_device}. Choose 'nanopick' or 'quickpick'.")










    

    