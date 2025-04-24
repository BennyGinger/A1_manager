from __future__ import annotations # Enable type annotation to be stored as string
from pathlib import Path

from pycromanager import Core
import numpy as np
import tifffile as tiff

from microscope_hardware.dmd.dmd_mask_factory import DEFAULT_SLM_NAME, DmdMask


class Dmd:
    """Class to control the DMD through pycromanager."""
    __slots__ = ('core', 'dmd_mask', 'slm_name')
    
    def __init__(self, core: Core, trigger_mode: str='ExternalBulb', slm_name: str = DEFAULT_SLM_NAME) -> None:
        self.core = core
        self.slm_name = slm_name
        self.dmd_mask = DmdMask(self.core, slm_name)
        # Initialize DMD with a fullON mask by default
        self.load_dmd_mask('fullON')
        self._set_trigger_mode(trigger_mode)

    def set_dmd_exposure(self, exposure_sec: int) -> None:
        """Set the DMD exposure time."""
        self.core.set_property(self.slm_name, 'ExposureTime', exposure_sec)
    
    def activate(self) -> None:
        """Activate the DMD by displaying the current mask."""
        self.core.display_slm_image(self.slm_name)
        
    def _project_mask(self, mask: np.ndarray)-> None:
        """Project the given mask on the DMD and activate it."""
        self.core.set_slm_image(self.slm_name, mask)
        self.activate()

    def _set_trigger_mode(self, trigger_mode: str)-> None:
        """
        Set the trigger mode of the DMD.
        Valid options include 'InternalExposure' (Manual) and 'ExternalBulb' (TTL).
        """
        self.core.set_property(self.slm_name,'TriggerMode',trigger_mode)

    def load_dmd_mask(self, input_mask: str | Path | np.ndarray='fullON', transform_mask: bool=True) -> np.ndarray:
        """
        Load a DMD mask from a string, file path, or numpy array, optionally transforming it,
        and project it to the DMD.
        """
        dmd_mask = self._get_dmd_mask(input_mask, transform_mask)
        # Project mask into DMD
        self._project_mask(dmd_mask)
        return dmd_mask
    
    def _get_dmd_mask(self, input_mask: str | Path | np.ndarray, transform_mask: bool=True)-> np.ndarray:
        """Create a DMD mask array from various input types."""
        if isinstance(input_mask, str):
            return self.dmd_mask.get_predefined_mask(input_mask)
        
        if isinstance(input_mask, Path):
            mask_array = tiff.imread(input_mask).astype(bool)
            return self.dmd_mask.custom_mask(mask_array, transform_mask)
        
        return self.dmd_mask.custom_mask(input_mask, transform_mask)
