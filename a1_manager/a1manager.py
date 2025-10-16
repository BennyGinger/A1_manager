from __future__ import annotations # Enable type annotation to be stored as string
from pathlib import Path
from time import sleep
import logging
from typing import Any
import warnings

# Suppress pycromanager version mismatch warning
warnings.filterwarnings("ignore", message=".*Java ZMQ server and Python client.*")

import numpy as np
from pycromanager import Core

from a1_manager import StageCoord
from a1_manager.microscope_hardware.nikon import NikonTi2
from a1_manager.microscope_hardware.cameras import AndorCamera
from a1_manager.microscope_hardware.dmd_manager import Dmd
from a1_manager.microscope_hardware.lamps_factory import get_lamp
from a1_manager.utils.json_utils import load_config_file


# TODO: Find a way to populate config file in parent pkg directory
OPTICAL_CONFIGURATION = load_config_file('optical_configuration')

IS_DMD_ATTACHED = {'pE-800': True, 'pE-4000': False, 'DiaLamp': False}

logger = logging.getLogger(__name__)


class A1Manager:
    """Class that allows any kind of aquisition with the A1_dmd. It is a wrapper around the Core, NikonTi2, AndorCamera and Dmd classes.
    It allows to set the optical configuration, snap images, and control the DMD and lamp.
    Args:
        objective (str): The objective to use. Must be one of '10x', '20x'.
        exposure_ms (float): The exposure time in milliseconds. Default is 100.
        binning (int): The binning factor. Default is 2.
        lamp_name (str): The name of the lamp to use. Must be one of 'pE-800', 'pE-4000', 'DiaLamp'. Default is 'pE-4000'.
        focus_device (str): The focus device to use. Must be one of 'ZDrive', 'PFSOffset'. Default is 'ZDrive'.
        dmd_trigger_mode (str): The trigger mode for the DMD. Must be one of 'InternalExpose', 'ExternalTrigger'. Default is 'InternalExpose'.
        """
    __slots__ = 'core', 'nikon', 'camera', 'dmd', 'lamp', 'activate_dmd', 'is_dmd_attached', 'trigger_mode', '_pfs_offset', '_is_pfs_disabled', '_cached_oc_state'
    
    def __init__(self, objective: str, exposure_ms: float=100, binning: int=2, lamp_name: str='pE-4000', focus_device: str='ZDrive', dmd_trigger_mode: str='InternalExpose') -> None:
        # Initialize Core bridge
        self.core = Core()
        
        self.nikon = NikonTi2(self.core, objective, focus_device) # type: ignore
        self._pfs_offset = True if focus_device == 'PFSOffset' else False
        self._is_pfs_disabled = False
        self.camera = AndorCamera(self.core, binning, exposure_ms) # type: ignore
        self.lamp = get_lamp(self.core, lamp_name) # type: ignore
        
        # Attach DMD to lamp
        self.dmd = None
        self.activate_dmd = False
        self.is_dmd_attached = IS_DMD_ATTACHED[lamp_name]
        self.trigger_mode = ''
        if self.is_dmd_attached:
            self.dmd = Dmd(self.core,dmd_trigger_mode) # type: ignore
            self.trigger_mode = dmd_trigger_mode
        
        # Initialize cache for optical configuration state
        self._cached_oc_state: dict[str, float | int | None] = {
            'exposure_ms': None,
            'light_path': None}
        
        
    def oc_settings(self, optical_configuration: str, intensity: float | None = None, exposure_ms: float | None = None, light_path: int | None = None)-> None:
        """Set the optical configuration for the microscope.
        
        Args:
        - optical_configuration (str): The optical configuration to set. Must be one of the keys in the OPTICAL_CONFIGURATION dictionary. e.g. 'GFP', 'RFP', etc.
        - intensity (float): optional, the intensity of the lamp. If None, it will use the default value from the optical configuration.
        - exposure_ms (float): optional, the exposure time in milliseconds. If None, it will use the default value from the optical configuration.
        - light_path (int): optional, the light path to use. If None, it will use the default value from the optical configuration.
        """
              
        # Set the filters and led settings for the optical configuration
        # oc = OPTICAL_CONFIGURATION[optical_configuration]
        cfg = OPTICAL_CONFIGURATION
        
        default_lp = cfg.get('light_path') if cfg is not None else None
        if default_lp is None:
            logger.warning("No global 'light_path' defined in optical_configuration; using 1 as fallback.")
            default_lp = 1
        
        channel_cfg: dict[str, Any] | None = cfg.get(optical_configuration) if cfg is not None else None
        if channel_cfg is None:
            logger.error(f"Optical configuration '{optical_configuration}' not found.")
            raise KeyError(f"Optical configuration '{optical_configuration}' not found.")
        
        # Extract exposure time from oc
        expo_ms: float = exposure_ms if exposure_ms is not None else channel_cfg.get('exposure_ms', 100.0)
        oc = {k: v for k, v in channel_cfg.items() if k not in ('exposure_ms', 'light_path')}
        
        # Determine final light path
        light_path = light_path if light_path is not None else default_lp
        
        # Validate light path
        if light_path not in [0,1,2,3]:
            logger.error(f"Invalid light path: {light_path}. Must be 0, 1, 2 or 3.")
            raise ValueError(f"Invalid light path: {light_path}. Must be 0, 1, 2 or 3.")
        
        # Only update camera exposure if it has changed
        if self._cached_oc_state['exposure_ms'] != expo_ms:
            self.camera.set_camera_exposure(expo_ms)
            self._cached_oc_state['exposure_ms'] = expo_ms

        # Set the lamp settings
        self.lamp.preset_channel(oc, intensity)
        
        # Only update light path if it has changed
        if self._cached_oc_state['light_path'] != light_path:
            self.nikon.set_light_path(light_path)  # Change Light path: 0=EYE, 1=R, 2=AUX and 3=L       
            self._cached_oc_state['light_path'] = light_path

    def clear_oc_cache(self) -> None:
        """Clear the optical configuration cache to force all settings to be reapplied on next call."""
        self._cached_oc_state = {
            'exposure_ms': None,
            'light_path': None}
        self.lamp.clear_lamp_cache()

    def set_dmd_exposure(self, dmd_exposure_sec: float=10)-> None:
        """Set the DMD exposure time."""
        if self.dmd is not None:
            self.dmd.set_dmd_exposure(dmd_exposure_sec)
            if self.trigger_mode == 'InternalExpose':
                self.dmd.activate()
    
    def load_dmd_mask(self, input_mask: str | Path | np.ndarray='fullON', transform_mask: bool=True) -> np.ndarray:
        """Load a DMD mask from a string, file path, or numpy array, optionally transforming it, and project it to the DMD."""
        return self.dmd.load_dmd_mask(input_mask,transform_mask) if self.dmd is not None else np.array([])
    
    def snap_image(self, dmd_exposure_sec: float=10)-> np.ndarray:
        """
        Snap an image with the camera and return it as a numpy array.
        """
        if self._is_pfs_disabled:
            logger.error(f"PFS initialization failed")
            image_size = (2048 // self.camera.binning, 2048 // self.camera.binning)
            return np.zeros(image_size, dtype='uint16')

        self.set_dmd_exposure(dmd_exposure_sec)
        
        # Snap image
        self.core.snap_image() # type: ignore
        # Convert im to array
        tag_img = self.core.get_tagged_image() # type: ignore
        img = tag_img.pix.reshape(tag_img.tags["Height"],tag_img.tags["Width"]).astype('uint16')
        
        return img
        
    def light_stimulate(self, duration_sec: float=10)-> None:
        """Turn on the lamp for a given duration."""
        # Illuminate, and keeps shutter open for exposure time
        if self._pfs_offset:
            try:
                self._pfs_initialization()
            except RuntimeError as e:
                logger.warning(f"PFS initialization failed during light stimulation: {e}")
                # Continue with stimulation even if PFS fails
        
        if self.dmd:
            self.set_dmd_exposure(duration_sec)
        
        if self.activate_dmd:
            self.dmd.activate() if self.dmd is not None else None
        
        self.lamp.set_LED_shutter(1)
        sleep(duration_sec) # Time in seconds
        self.lamp.set_LED_shutter(0)
    
    def set_stage_position(self, stage_position: StageCoord)-> None:
        """
        Set the stage position in XY coordinates and the focus device position.
        Args:
            stage_position (StageCoord): StageCoord object containing the XY coordinates and the focus device position.
        """
        self.nikon.set_stage_position(stage_position)
        
        if self._pfs_offset:
            self._pfs_initialization()
    
    def _size_pixel2micron(self, size_in_pixel: int | None = None)-> float:
        """Convert size from pixel to micron. Return the size in float."""
        pixel_calibration = {'10x':0.6461,'20x':0.3258}
        objective = self.nikon.objective
        binning = self.camera.binning
        pixel_in_um = pixel_calibration[objective]
        if size_in_pixel:
            return size_in_pixel*pixel_in_um*binning
        image_size = (2048 // binning, 2048 // binning)
        return image_size[0]*pixel_in_um*binning
    
    @property
    def image_size(self)-> tuple[int,int]:
        """Calculate window size in pixel for the camera."""
        return (2048//self.camera.binning, 2048//self.camera.binning)
    
    def window_size(self, dmd_window_only: bool)-> tuple[int,int]:
        """Calculate window size in micron for the camera."""
        
        if self.is_dmd_attached and dmd_window_only and self.dmd is not None:
            dmd_size = self.dmd.dmd_mask.dmd_size
            return (int(self._size_pixel2micron(dmd_size[0])),int(self._size_pixel2micron(dmd_size[1])))
        return (int(self._size_pixel2micron(self.image_size[0])),int(self._size_pixel2micron(self.image_size[1])))
    
    def _pfs_initialization(self, max_retries: int = 5)-> None:
        """
        Initialize the PFS system with retry logic for different statuses.
        """
        # PFS Status codes
        PFS_ON = '0000001100001010'      # PFS is on and working
        PFS_OFF = '0000000100000000'     # PFS is off but can be turned on
        PFS_WAITING = '0000001100001001'
        PFS_DISABLED = '0010001000001001'  # PFS is disabled
        
        for _ in range(max_retries):
            current_status = self.core.get_property('PFS','PFS Status') # type: ignore
            
            if current_status == PFS_ON:
                # PFS is already on and working
                return 
            
            elif current_status == PFS_OFF:
                # PFS is off, try to turn it on
                self.core.set_property('PFS','FocusMaintenance','On') # type: ignore
                sleep(0.1)  # Give it some time to initialize
            
            elif current_status == PFS_WAITING:
                # PFS is waiting, give it some time
                sleep(0.4)
               
            elif current_status == PFS_DISABLED:
                # PFS is disabled, try to enable and turn on
                self.core.set_property('PFS','FocusMaintenance','On') # type: ignore
                sleep(0.4)  # Give it more time when recovering from disabled state
                
            else:
                # Unknown status
                self.core.set_property('PFS','FocusMaintenance','On') # type: ignore
                sleep(0.4)
        # If we get here, all attempts failed
        self._is_pfs_disabled = True
        


if __name__ == "__main__":
    # Example usage
    a1_manager = A1Manager(objective='20x', exposure_ms=150, binning=2, lamp_name='pE-800')
    a1_manager.core.set_property('PFS','FocusMaintenance','On') # type: ignore
    print(a1_manager.core.get_property('PFS','PFS Status')) # type: ignore