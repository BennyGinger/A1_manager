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

logging.basicConfig(
    level=logging.INFO, # Set the logging level to INFO, other options: DEBUG, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("microscope_control.log")
    ]
)

class A1Manager:
    """ Class that allows any kind of aquisition with the A1_dmd."""
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
    
    def oc_settings(self, optical_configuration: str, intensity: float | None = None, exposure_ms: float | None = None)-> None:
        """Set the optical configuration for the microscope."""
        # Set the filters and led settings for the optical configuration
        oc = OPTICAL_CONFIGURATION[optical_configuration]
        
        # Extract exposure time from oc
        if exposure_ms is None:
            exposure_ms = oc['exposure_ms']
        oc = {k:v for k, v in oc.items() if k != 'exposure_ms'}
        
        # Set the camera exposure
        self.camera.set_camera_exposure(exposure_ms)
        
        # Set the lamp settings
        self.lamp.preset_channel(oc, intensity)
        # TODO: Note from Raph: Do we really want this hardcoded? -> into config file
        self.nikon.set_light_path(1) # Change Light path: 0=EYE, 1=R, 2=AUX and 3=L
        
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
    
    # TODO: Convert to a static method
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