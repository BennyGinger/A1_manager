from skimage.transform import resize
from cv2 import warpAffine
from pycromanager import Core
import numpy as np

from utils.utils import load_config_file

# Device constants for easy configuration
DEFAULT_SLM_NAME = 'Mosaic3'
DEFAULT_FILTER_TURRET_NAME = 'FilterTurret1'

class DMDMask:
    """Class for generating and transforming masks for the DMD."""
    __slots__ = ('core', 'slm_name', 'dmd_size', 'transfo_matrix', 'filter_turret_name')
    def __init__(self, core: Core, slm_name: str = DEFAULT_SLM_NAME, filter_turret_name: str = DEFAULT_FILTER_TURRET_NAME) -> None:
        self.core = core
        self.slm_name = slm_name
        self.filter_turret_name = filter_turret_name
        # Get DMD size == (x,y)
        self.dmd_size = (self.core.get_slm_width(self.slm_name), self.core.get_slm_height(self.slm_name))
        self.transfo_matrix = load_config_file('transfo_matrix')
    
    def get_predefined_mask(self, mask_type: str) -> np.ndarray:
        """
        Return a predefined mask.
        Supported types:
          - 'fullON': a mask with all elements set to one.
          - 'fullOFF': a mask with all elements set to zero.
        """
        if mask_type == 'fullON':
            return np.ones(self.dmd_size, dtype='uint8')
        elif mask_type == 'fullOFF':
            return np.zeros(self.dmd_size, dtype='uint8')
        else:
            raise ValueError(f"Unknown mask type: {mask_type}")
    
    def custom_mask(self, mask_array: np.ndarray, transform_mask: bool)-> np.ndarray:
        """
        Optionally apply an affine transformation to the mask, flip its orientation,
        and scale it to match the DMD size.
        """
        if transform_mask:
            mask_array = self.apply_affine_transform(mask_array)
        
        # Flip mask to match dmd orientation
        mask_array = np.flipud(mask_array)
        # Resize array to dmd size
        return self._scale_down_array(mask_array,(self.dmd_size))
    
    def apply_affine_transform(self, mask: np.ndarray, custom_matrix: dict = None)-> np.ndarray:
        """
        Apply an affine transformation to the mask.
        If a custom matrix is provided, it is used; otherwise, the preloaded transformation matrix is applied.
        """
        turret_label = self.core.get_property(self.filter_turret_name, 'Label')
        if custom_matrix is not None:
            tmat = np.array(custom_matrix.get(turret_label))
        else:
            tmat = np.array(self.transfo_matrix.get(turret_label))
        if tmat is None:
            raise ValueError(f"No transformation matrix found for turret label: {turret_label}")
        transformed = warpAffine(mask.astype('uint8'), tmat, mask.shape)
        return transformed.astype('uint16')
    
    def reload_transformation_matrix(self) -> None:
        """
        Reload the transformation matrix from file.
        """
        self.transfo_matrix = load_config_file('transfo_matrix')

    @staticmethod
    def _scale_down_array(array: np.ndarray, target_size: tuple[int,int])-> np.ndarray:
        target_width, target_height = target_size
        
        if target_height < target_width:
            # Resize array to dmd width
            scaled_array = resize(array, (target_width, target_width)).astype(bool)
        
            # Crop to dmd height
            starty = target_width // 2 - (target_height // 2)
            return scaled_array[starty:starty + target_height, :].astype('uint8')
        else:
            # Resize array to dmd height
            scaled_array = resize(array, (target_height, target_height)).astype(bool)
        
            # Crop to dmd width
            startx = target_height // 2 - (target_width // 2)
            return scaled_array[:, startx:startx + target_width].astype('uint8')
