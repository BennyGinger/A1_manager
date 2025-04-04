from __future__ import annotations # Enable type annotation to be stored as string
from pathlib import Path

from pycromanager import Studio
from tifffile import imwrite
import numpy as np

from main import A1Manager


class MMAutoFocus:
    """Class to control the autofocus through pycromanager."""
    
    __slots__ = 'method','core','normalisation'
    
    def __init__(self, a1_manager: A1Manager) -> None:
        # Initiate autofocus manager
        self.method = 'OughtaFocus'
        self.core = a1_manager.core
        
        # Set focus device to ZDrive
        a1_manager.nikon.select_zStage('ZDrive')
        
        # Set normalisation
        self.normalisation = 'FFTBandpass'
        if a1_manager.lamp_name=='DiaLamp':
            self.normalisation = 'NormalizedVariance' 
    
    def _load_method(self, searchRange: int)-> Studio:
        # Create Autofocus manager
        autofocus_manager = Studio().get_autofocus_manager()
        # Get autofocus method
        autofocus_manager.set_autofocus_method_by_name(self.method)
        afm_method = autofocus_manager.get_autofocus_method()
        # Load method settings
        return self._oughtaFocus(afm_method, searchRange, self.normalisation)
    
    def find_focus(self, searchRange: int=500)-> float:
        """searchRange and step in micron if Zdrive and arbitrary unit (0-12000) if PFS"""
        # Load method
        afm_method = self._load_method(searchRange)
        # Start autofocus
        afm_method.full_focus()
        return self.core.get_position()
    
    @staticmethod
    def _oughtaFocus(afm_method: Studio, searchRange: int=100, normalisation: str='FFTBandpass')-> Studio: 
        # Set properties
        ## Fixed prop.
        afm_method.set_property_value('ShowImages', 'No') #determines whether images will be displayed in the Live Window during the autofocus routine.
        afm_method.set_property_value('Channel', '') #allows you to select a channel preset to be used for autofocus – if no Channel is selected, then the current hardware settings will be used.
        afm_method.set_property_value('FFTLowerCutoff(%)', '2.5')
        afm_method.set_property_value('FFTUpperCutoff(%)', '14')
        afm_method.set_property_value('CropFactor', '1') #The plugin will apply a camera ROI to the center of the field of view during autofocus, to reduce the time required to read out each image. A CropFactor of 1 means that the entire field will be used.
        afm_method.set_property_value('Tolerance_um', '0.2') #Search will stop when the z position’s distance from maximum focus quality is estimated to be within the tolerance specified.
        afm_method.set_property_value('Exposure', '200') # specifies how long the plugin will expose each image during the autofocus routine.
        ## User input prop.
        afm_method.set_property_value('SearchRange_um', str(searchRange)) #OughtaFocus will search over z range specified, centered at the current z position.
        afm_method.set_property_value('Maximize', normalisation) #determines what property of the autofocusing image series will be used to evaluate the quality of focus. You can choose Mean, Standard Deviation, or Edges (a function that looks at the variance of the first derivative). Experiment with different methods to find the best one for your sample.
        # 'NormalizedVariance' for bf and 'FFTBandpass' for fluorescence
        return afm_method

class SqGradAutoFocus:
    """Class the control the autofocus through the squared gradient method."""
    
    __slots__ = 'a1_manager'
    
    def __init__(self, a1_manager: A1Manager) -> None: 
        self.a1_manager = a1_manager
    
    def _determine_range_step(self, searchRange: int, step: int)-> list[float]:
        """searchRange and step in micron if Zdrive and arbitrary unit (0-12000) if PFS"""
        
        current_position = self.a1_manager.nikon.get_stage_position()
        focus_device = self.a1_manager.core.get_property('Core','Focus') # ZDrive, PFSOffset, MarZ
        current_z = current_position[focus_device]
        searchRange_offset = searchRange / 2
        start = current_z - searchRange_offset
        end = current_z + searchRange_offset + step
        return np.arange(start, end, step) 
    
    def _capture_images_at_z(self, z_positions: list[float])-> list[np.ndarray]:
        """Create a list of images at different z positions."""
        
        img_list = []
        for z in z_positions:
            # Move to the z position
            self.a1_manager.core.set_position(z)
            img_list.append(self.a1_manager.snap_image())
        return img_list

    def find_focus(self, searchRange: int, step: int, savedir: Path | None)-> float:
        """searchRange and step in micron if Zdrive and arbitrary unit (0-12000) if PFS"""
        # Determine the z positions to image
        z_positions = self._determine_range_step(searchRange,step)
        # Image the z positions
        img_list = self._capture_images_at_z(z_positions)
        # Find the best focus
        focus_value_list = []
        for idx, img in enumerate(img_list):
            focus_val = self._sq_grad(img)
            focus_value_list.append(focus_val)
            if savedir is not None:
                imwrite(savedir.joinpath(f"af_im{idx+1}_{focus_val}.tiff"), img)
        
        focus_point = z_positions[np.argmax(focus_value_list)]
        return focus_point

    @staticmethod
    def _sq_grad(img: np.ndarray) -> int:
        """Calculate the squared gradient of the image. The higher the value, the better the focus. Found in algorithm for finding the best focus taken from https://doi.org/10.1002/jemt.24035"""
        
        threshold = 51
        img = img.astype(np.int64)
        # Calculate differences along x-axis
        diff = np.diff(img, axis=1)
        # Apply threshold and compute squared sum
        mask = np.abs(diff) >= threshold
        return int(np.sum((diff[mask]) ** 2))

class ManualFocus:
    """Class to set the focus manually. The user will have to focus to the best position before the autofocus function is called."""
    
    __slots__ = 'a1_manager'
    
    def __init__(self, a1_manager: A1Manager) -> None: 
        self.a1_manager = a1_manager
    
    def find_focus(self)-> float:
        """searchRange and step in micron if Zdrive and arbitrary unit (0-12000) if PFS"""
        current_position = self.a1_manager.nikon.get_stage_position()
        focus_device = self.a1_manager.core.get_property('Core','Focus') # ZDrive, PFSOffset, MarZ
        return current_position[focus_device]
