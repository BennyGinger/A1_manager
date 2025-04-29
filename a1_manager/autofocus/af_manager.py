from __future__ import annotations # Enable type annotation to be stored as string
from pathlib import Path

from autofocus.af_mtds import MMAutoFocus, SqGradAutoFocus, ManualFocus
from a1_manager.a1manager import A1Manager


class AutoFocusManager:
    """Class to manage the autofocus process, given the autofocus method."""
    
    __slots__ = ('a1_manager','method','autofocus','savedir')
    
    _method_mapping = {
        'sq_grad': SqGradAutoFocus,
        'OughtaFocus': MMAutoFocus,
        'Manual': ManualFocus,}
    
    def __init__(self, a1_manager: A1Manager, method: str, savedir: Path=None) -> None: 
        self.a1_manager = a1_manager
        self.method = method
        self.savedir = savedir
        
        # Load autofocus method object
        if method not in self._method_mapping:
            raise ValueError(f"Method {method} not found. Choose from {list(self._method_mapping.keys())}")
        
        self.autofocus = self._method_mapping[method](a1_manager)
    
    def find_focus(self, searchRange: int=500, step: int=50)-> float:
        """Find the best focus point using the autofocus method."""
        input_settings = {}
        if self.method != 'Manual':
            input_settings = {'searchRange':searchRange}
        if self.method=='sq_grad':
            input_settings['step'] = step
            input_settings['savedir'] = self.savedir
        
        focus_point = self.autofocus.find_focus(**input_settings)
        focus_device = self.a1_manager.core.get_property('Core', 'Focus') # ZDrive, PFSOffset, MarZ
        self.a1_manager.core.set_position(focus_device, focus_point)
        return focus_point
