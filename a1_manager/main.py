from pathlib import Path
from time import sleep

import numpy as np
from pycromanager import Core

from microscope_hardware.nikon import NikonTi2
from microscope_hardware.cameras import AndorCamera
from microscope_hardware.dmd_manager import DMD 
from microscope_hardware.lamps_factory import get_lamp
from utils.utils import load_file

# TODO: Correct the Turret filter for all channels

OPTICAL_CONFIGURATION = load_file('optical_configuration')

IS_DMD_ATTACHED = {'pE-800': True, 'pE-4000': False, 'DiaLamp': False}

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
            self.dmd = DMD(self.core,dmd_trigger_mode)
    
    def oc_settings(self, optical_configuration: str, intensity: float | None = None, exposure_ms: float | None = None)-> None:
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
        self.nikon.set_light_path(1) # Change Light path: 0=EYE, 1=R, 2=AUX and 3=L
        
        # Swith the lappMainBranch to the correct position
        if self.lamp.lamp_main_branch is not None:
            self.core.set_property('LappMainBranch1', 'State', self.lamp.lamp_main_branch)

    def set_dmd_exposure(self, dmd_exposure_sec: float=10)-> None:
        self.dmd.set_dmd_exposure_sec(dmd_exposure_sec)
        if self.core.get_property('Mosaic3','TriggerMode')=='InternalExpose':
            self.dmd.activate()
    
    def load_dmd_mask(self, input_mask: str | Path | np.ndarray='fullON', transform_mask: bool=True) -> np.ndarray:
        return self.dmd.load_dmd_mask(input_mask,transform_mask)
    
    def snap_image(self, dmd_exposure_sec: float=10)-> np.ndarray: 
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
    
    def _pfs_initialization(self)-> None:
        while True:  # Make sure that PFS is on, before snap
            if self.core.get_property('PFS','PFS Status') == '0000001100001010':
                break