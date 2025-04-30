from __future__ import annotations # Enable type annotation to be stored as string
from pathlib import Path
from time import sleep

import numpy as np
from pycromanager import Core
import logging

from microscope_hardware.nikon import NikonTi2
from microscope_hardware.cameras import AndorCamera
from microscope_hardware.dmd_manager import Dmd
from microscope_hardware.lamps_factory import get_lamp
from utils.utils import load_config_file


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
    __slots__ = 'core', 'nikon', 'camera', 'dmd', 'lamp', 'activate_dmd', 'is_dmd_attached'
    
    def __init__(self, objective: str, exposure_ms: float=100, binning: int=2, lamp_name: str='pE-4000', focus_device: str='ZDrive', dmd_trigger_mode: str='InternalExpose') -> None:
        # Initialize Core bridge
        self.core = Core()
        
        self.nikon = NikonTi2(self.core, objective, focus_device)
        self.camera = AndorCamera(self.core, binning, exposure_ms)
        self.lamp = get_lamp(self.core, lamp_name)
        
        # Attach DMD to lamp
        self.dmd = None
        self.activate_dmd = False
        self.is_dmd_attached = IS_DMD_ATTACHED[lamp_name]
        if self.is_dmd_attached:
            self.dmd = Dmd(self.core,dmd_trigger_mode)
    
    def oc_settings(self, optical_configuration: str, intensity: float | None = None, exposure_ms: float | None = None, light_path: int | int = None)-> None:
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
        
        default_lp = cfg.get('light_path')
        if default_lp is None:
            logger.warning("No global 'light_path' defined in optical_configuration; using 1 as fallback.")
            default_lp = 1
        
        channel_cfg = cfg.get(optical_configuration)
        if channel_cfg is None:
            logger.error(f"Optical configuration '{optical_configuration}' not found.")
            raise KeyError(f"Optical configuration '{optical_configuration}' not found.")
        
        # Extract exposure time from oc
        if exposure_ms is None:
            exposure_ms = channel_cfg.get('exposure_ms')
        oc = {k: v for k, v in channel_cfg.items() if k not in ('exposure_ms', 'light_path')}
        
        # Set the camera exposure
        self.camera.set_camera_exposure(exposure_ms)
        
        # Set the lamp settings
        self.lamp.preset_channel(oc, intensity)
        
        light_path = light_path if light_path is not None else default_lp
        
        # Set the light path
        if light_path not in [0,1,2,3]:
            logger.error(f"Invalid light path: {light_path}. Must be 0, 1, 2 or 3.")
            raise ValueError(f"Invalid light path: {light_path}. Must be 0, 1, 2 or 3.")
        
        self.nikon.set_light_path(light_path)  # Change Light path: 0=EYE, 1=R, 2=AUX and 3=L       
        logger.debug(f"Set light path to {light_path} for configuration '{optical_configuration}'.")
    
    
        # Swith the lappMainBranch to the correct position
        if self.lamp.lapp_main_branch is not None:
            self.core.set_property('LappMainBranch1', 'State', self.lamp.lapp_main_branch)

    def set_dmd_exposure(self, dmd_exposure_sec: float=10)-> None:
        """Set the DMD exposure time."""
        self.dmd.set_dmd_exposure(dmd_exposure_sec)
        if self.core.get_property('Mosaic3','TriggerMode')=='InternalExpose':
            self.dmd.activate()
    
    def load_dmd_mask(self, input_mask: str | Path | np.ndarray='fullON', transform_mask: bool=True) -> np.ndarray:
        """Load a DMD mask from a string, file path, or numpy array, optionally transforming it, and project it to the DMD."""
        return self.dmd.load_dmd_mask(input_mask,transform_mask)
    
    def snap_image(self, dmd_exposure_sec: float=10)-> np.ndarray:
        """Snap an image with the camera and return it as a numpy array."""
        if self.dmd:
            self.set_dmd_exposure(dmd_exposure_sec)
            
        if self.core.get_property('Core','Focus')=='PFSOffset':
            self._pfs_initialization()
        # Snap image
        self.core.snap_image()
        # Convert im to array
        tag_img = self.core.get_tagged_image()
        img = tag_img.pix.reshape(tag_img.tags["Height"],tag_img.tags["Width"]).astype('uint16')
        
        return img
        
    def light_stimulate(self, duration_sec: float=10)-> None:
        """Turn on the lamp for a given duration."""
        # Illuminate, and keeps shutter open for exposure time
        if self.core.get_property('Core','Focus')=='PFSOffset':
            self._pfs_initialization()
        
        if self.dmd:
            self.set_dmd_exposure(duration_sec)
        
        if self.activate_dmd:
            self.dmd.activate()
        
        self.lamp.set_LED_shutter(1)
        sleep(duration_sec) # Time in seconds
        self.lamp.set_LED_shutter(0)
    
    def _size_pixel2micron(self, size_in_pixel: int=None)-> float:
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
        
        if self.is_dmd_attached and dmd_window_only:
            dmd_size = self.dmd.dmd_mask.dmd_size
            return (self._size_pixel2micron(dmd_size[0]),self._size_pixel2micron(dmd_size[1]))
        return (self._size_pixel2micron(self.image_size[0]),self._size_pixel2micron(self.image_size[1]))
    
    def _pfs_initialization(self)-> None:
        """Initialize the PFS system."""
        while True:  # Make sure that PFS is on, before snap
            if self.core.get_property('PFS','PFS Status') == '0000001100001010':
                break


if __name__ == "__main__":
    # Example usage
    run_dir = Path('D:\\Raph\\test_lib')
    a1_manager = A1Manager(objective='20x', exposure_ms=150, binning=2, lamp_name='pE-800')
    a1_manager.oc_settings(optical_configuration='GFP', intensity=10)
    a1_manager.light_stimulate(duration_sec=10)
    image = a1_manager.snap_image(dmd_exposure_sec=10)
    print(image.shape)