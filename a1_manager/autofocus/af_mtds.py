from os.path import join

from pycromanager import Studio
from tifffile import imwrite
import numpy as np

from main import A1Manager


class MMAutoFocus:
    """Class to control the autofocus through pycromanager."""
    __slots__ = 'afm','method','core','normalisation'
    
    def __init__(self, a1_manager: A1Manager, method: str='OughtaFocus') -> None:
        # Initiate autofocus manager
        self.method = method
        self.core = a1_manager.core
        # Set focus device to ZDrive
        self.aquisition.nikon.select_zStage('ZDrive')
        # Set normalisation
        self.normalisation = 'FFTBandpass'
        if a1_manager.lamp_name=='DiaLamp':
            self.normalisation = 'NormalizedVariance'
    
    def load_method(self, searchRange: int)-> Studio.CoreAutofocus:
        # Create Autofocus manager
        autofocus_manager = Studio().get_autofocus_manager()
        # Get autofocus method
        autofocus_manager.set_autofocus_method_by_name(self.method)
        afm_method = self.afm.get_autofocus_method()
        # Load method settings
        if self.method=='OughtaFocus':
            return self.oughtaFocus(afm_method,searchRange,self.normalisation)
   
    def find_focus(self, searchRange: int=500)-> float:
        """searchRange and step in micron if Zdrive and arbitrary unit (0-12000) if PFS"""
        # Load method
        afm_method = self.load_method(searchRange)
        # Start autofocus
        afm_method.full_focus()
        return self.core.get_position()
    
    @staticmethod
    def oughtaFocus(afm_method: Studio.CoreAutofocus, searchRange: int=100, normalisation: str='FFTBandpass')-> Studio.CoreAutofocus: 
        # Set properties
        ## Fixed prop.
        afm_method.set_property_value('ShowImages','No') #determines whether images will be displayed in the Live Window during the autofocus routine.
        afm_method.set_property_value('Channel','') #allows you to select a channel preset to be used for autofocus – if no Channel is selected, then the current hardware settings will be used.
        afm_method.set_property_value('FFTLowerCutoff(%)','2.5')
        afm_method.set_property_value('FFTUpperCutoff(%)','14')
        afm_method.set_property_value('CropFactor','1') #The plugin will apply a camera ROI to the center of the field of view during autofocus, to reduce the time required to read out each image. A CropFactor of 1 means that the entire field will be used.
        afm_method.set_property_value('Tolerance_um','0.2') #Search will stop when the z position’s distance from maximum focus quality is estimated to be within the tolerance specified.
        afm_method.set_property_value('Exposure','200') # specifies how long the plugin will expose each image during the autofocus routine.
        ## User input prop.
        afm_method.set_property_value('SearchRange_um',str(searchRange)) #OughtaFocus will search over z range specified, centered at the current z position.
        afm_method.set_property_value('Maximize',normalisation) #determines what property of the autofocusing image series will be used to evaluate the quality of focus. You can choose Mean, Standard Deviation, or Edges (a function that looks at the variance of the first derivative). Experiment with different methods to find the best one for your sample.
        # 'NormalizedVariance' for bf and 'FFTBandpass' for fluorescence
        return afm_method
    
class FabAutoFocus:
    __slots__ = 'aquisition','focus_method'
    def __init__(self, a1_manager: A1Manager, method: str='sq_grad') -> None: 
        self.aquisition = a1_manager
        if method=='sq_grad':
            self.focus_method = self.sq_grad
        
    def determine_range_step(self, searchRange: int, step: int)-> list[float]:
        """searchRange and step in micron if Zdrive and arbitrary unit (0-12000) if PFS"""
        current_position = self.aquisition.nikon.get_stage_position()
        focus_device = self.aquisition.core.get_property('Core','Focus') # ZDrive, PFSOffset, MarZ
        current_z = current_position[focus_device]
        return np.arange(current_z-searchRange/2,current_z+searchRange/2+step,step) 
    
    def autofocus_imaging(self, z_positions: list[float])-> list[np.ndarray]:
        img_list = []
        for z in z_positions:
            # Move to the z position
            self.aquisition.core.set_position(z)
            img_list.append(self.aquisition.snap_image())
        return img_list

    def find_focus(self, searchRange: int, step: int, savedir: str)-> float:
        """searchRange and step in micron if Zdrive and arbitrary unit (0-12000) if PFS"""
        # Determine the z positions to image
        z_positions = self.determine_range_step(searchRange,step)
        # Image the z positions
        img_list = self.autofocus_imaging(z_positions)
        # Find the best focus
        focus_value_list = []
        for i,img in enumerate(img_list):
            focus_val = self.focus_method(img)
            focus_value_list.append(focus_val)
            if savedir:
                imwrite(join(savedir,f"af_im{i+1}_{focus_val}.tiff"),img)
        
        focus_point = z_positions[np.argmax(focus_value_list)]
        return focus_point

    # algorithm for finding the best focus taken from https://doi.org/10.1002/jemt.24035
    @staticmethod
    def sq_grad(img: np.ndarray)-> int:
        # Recommendation form thres: 8bit: 51 or 16bit: 13105, However, eventhough our images are 16bits, it didn't work well, so we use 51, which worked
        threshold = 51
        pixel_in_y,pixel_in_x = img.shape
        img = np.int64(img)
        sum2 = 0
        for j in range(pixel_in_y - 1):
            sum1 = abs(img[:, j + 1] - img[:, j])
            for i in range(pixel_in_x):
                if sum1[i] >= threshold:
                    sum2 = sum2 + sum1[i] ** 2
        return sum2

class ManualFocus:
    __slots__ = 'aquisition'
    def __init__(self, a1_manager: A1Manager) -> None: 
        self.aquisition = a1_manager
    
    def find_focus(self, savedir: str)-> float:
        """searchRange and step in micron if Zdrive and arbitrary unit (0-12000) if PFS"""
        current_position = self.aquisition.nikon.get_stage_position()
        focus_device = self.aquisition.core.get_property('Core','Focus') # ZDrive, PFSOffset, MarZ
        return current_position[focus_device]