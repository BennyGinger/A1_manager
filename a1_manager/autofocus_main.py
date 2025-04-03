from __future__ import annotations # Enable type annotation to be stored as string
from pathlib import Path

from matplotlib import pyplot as plt

from main import A1Manager
from a1_manager.autofocus.af_manager import AutoFocusManager
from autofocus.af_utils import load_file, save_file
from utils.utility_classes import StageCoord, WellCircleCoord, WellSquareCoord


LARGE_FOCUS_RANGE = {
    'ZDrive':{'searchRange':1000, 'step':100},
    'PFSOffset':{'searchRange':4000, 'step':300}
}

SMALL_FOCUS_RANGE = {
    'ZDrive':{'searchRange':200, 'step':10},
    'PFSOffset':{'searchRange':1000, 'step':100}
}

def run_autofocus(method: str, a1_manager: A1Manager, calib_path: Path, overwrite: bool, af_savedir: Path=None)-> dict[str, WellCircleCoord | WellSquareCoord] | None:
        """
        Run autofocus for the selected wells. Requires the calibration file with the dish measurements.
        Dish measurements are in the form of a dict with well names as keys and dict of {'radius':rad,'center':(x_center, y_center),'ZDrive':None,'PFSOffset':None} as values.
        If the autofocus has failed, the user can restart the process without exiting.
        
        Args:
            method (str): Autofocus method to use. Choose from 'sq_grad', 'OughtaFocus', 'Manual'.
            a1_manager (A1Manager): A1Manager object.
            calib_path (Path): Path to the calibration file.
            overwrite (bool): If True, overwrite the focus values in the calibration file.
            af_savedir (Path): Path to save the images for the square gradient method.
        
        Returns:
            The updated dish measurements with the focus values. If the user quits the process, None is returned.
        """
        
        # Initialize focus device
        focus_device = a1_manager.core.get_property('Core', 'Focus')
        print(f'\nAutofocus with {focus_device} using {method} method')
        a1_manager.nikon.select_focus_device(focus_device)
        
        # Load dish measurements
        dish_measurements: dict[str, WellCircleCoord | WellSquareCoord] = load_file(calib_path)
        autofocus = AutoFocusManager(a1_manager, method, af_savedir) 
        
        while True:    
            # Run autofocus
            for idx, (well, measurement) in enumerate(dish_measurements.items()):
                print(f'\nAutofocus for well {well}')
                
                if measurement[focus_device] is not None and not overwrite:
                    print(f"Autofocus already done for {well} with {focus_device} at {measurement[focus_device]}")
                    continue
                    
                # Move to center of well
                point_center = StageCoord(xy=measurement['center'])
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
                    resp = input("If focus is good press enter, else type 'r' to restart or 'q' to quit: ")
                    if resp.lower() == 'q':
                        # Exit autofocus process
                        print("Exiting autofocus process...\n")
                        return None
                    elif resp.lower() == 'r':
                        # Will restart from the for loop
                        print("Restarting autofocus process...\n")
                        break
                
                # Update dish measurements  
                measurement[focus_device] = focus
            
            # Only triggered if the loop completes
            else:
                # Save dish measurements and exit
                save_file(calib_path, dish_measurements)
                return dish_measurements
