import json
from pathlib import Path

from autofocus.af_mtds import MMAutoFocus, FabAutoFocus, ManualFocus
from main import A1Manager


class AutoFocus:
    __slots__ = 'aquisition','method','autofocus','savedir'
    
    def __init__(self, a1_manager: A1Manager, method: str, savedir: str="") -> None: 
        self.aquisition = a1_manager
        self.method = method
        self.savedir = savedir
        # Load autofocus method object
        if method=='sq_grad':
            self.autofocus = FabAutoFocus(a1_manager,method)
        elif method=='OughtaFocus':
            self.autofocus = MMAutoFocus(a1_manager,method)
        elif method=='Manual':
            self.autofocus = ManualFocus(a1_manager)
    
    def find_focus(self, searchRange: int=500, step: int=50)-> float:
        input_settings = {}
        if self.method!='Manual':
            input_settings = {'searchRange':searchRange}
        if self.method=='sq_grad':
            input_settings['step'] = step
        focus_point = self.autofocus.find_focus(**input_settings,savedir=self.savedir)
        focus_device = self.aquisition.core.get_property('Core','Focus') # ZDrive, PFSOffset, MarZ
        self.aquisition.core.set_position(focus_device,focus_point)
        return focus_point
 

def load_config_file(calib_path: Path)-> dict:
    with open(calib_path) as f:
        return json.load(f)

def save_config_file(calib_path: Path, data: dict)-> None:
    with open(calib_path,'w') as f:
        json.dump(data,f)





