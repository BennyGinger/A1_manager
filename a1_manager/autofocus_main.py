from pathlib import Path

from matplotlib import pyplot as plt

from main import A1Manager
from autofocus.af_main import AutoFocus
from autofocus.af_utils import load_config_file, save_config_file


LARGE_FOCUS_RANGE = {'ZDrive':{'searchRange':1000, 'step':100},
               'PFSOffset':{'searchRange':4000, 'step':300}}

SMALL_FOCUS_RANGE = {'ZDrive':{'searchRange':200, 'step':10},
               'PFSOffset':{'searchRange':1000, 'step':100}}

def run_autofocus(method: str, a1_manager: A1Manager, calib_path: Path, well_selection: str | list[str], overwrite: bool, savedir: Path=None)-> bool:
        """Run autofocus for the selected wells. Requires the calibration file with the dish measurements. Dish measurements are in the form of a dict with well names as keys and dict of {'radius':rad,'center':(x_center, y_center),'ZDrive':None,'PFSOffset':None} as values.
        
        Args:
            method (str): Autofocus method to use. Choose from 'sq_grad', 'OughtaFocus', 'Manual'.
            a1_manager (A1Manager): A1Manager object.
            calib_path (Path): Path to the calibration file.
            well_selection (list[str]): List of well names to autofocus.
            overwrite (bool): If True, overwrite the focus values in the calibration file.
            savedir (Path): Path to save the images for the square gradient method.
            
        Returns:
            bool: True if the autofocus was complete, False otherwise.
        """
            
            
        # Initialize focus device
        focus_device = a1_manager.core.get_property('Core', 'Focus')
        print(f'\nAutofocus with {focus_device} using {method} method')
        a1_manager.nikon.select_focus_device(focus_device)
        
        # Load dish measurements
        dish_measurments = load_config_file(calib_path)
        autofocus = AutoFocus(a1_manager, method, savedir)
        
        # Setup the different wells
        if isinstance(well_selection, str):
            if well_selection == 'all':
                wells = list(dish_measurments.keys())
            else:
                wells = [well_selection]
        else:
            wells = well_selection
        
        # Run autofocus
        for idx, well in enumerate(wells):
        
            if dish_measurments[well][focus_device] and not overwrite:
                print(f"Autofocus already done for {well} with {focus_device} at {dish_measurments[well][focus_device]}")
                continue
                
            # Move to center of well
            point_center = {'xy': dish_measurments[well]['center'], 'ZDrive': None, 'PFSOffset': None}
            a1_manager.nikon.set_stage_position(point_center)

            # If first well, apply large focus range only for square gradient method
            if idx == 0 and method != 'Manual':
                print(f'Apply large focus range for {focus_device} in the center of well')
                autofocus.find_focus(**LARGE_FOCUS_RANGE[focus_device])
            
            # Apply fine focus range
            print(f'Fine tuned autofocus with {focus_device} in the center of well')
            focus = autofocus.find_focus(**SMALL_FOCUS_RANGE[focus_device])
            print(f'Focus value: {focus}')
            
            # If first well, show the image
            if idx == 0:
                img = a1_manager.snap_image(display=True)
                plt.imshow(img)
                plt.show()
                resp = input("If focus is good press enter, else type 'q': ")
                if resp == 'q':
                    return False
            
            # Update dish measurements  
            dish_measurments[well][focus_device] = focus
        
        # Save dish measurements
        save_config_file(calib_path, dish_measurments)
        return True