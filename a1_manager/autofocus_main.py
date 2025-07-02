from __future__ import annotations # Enable type annotation to be stored as string
from pathlib import Path

from matplotlib import pyplot as plt
import logging

from a1_manager.a1manager import A1Manager
from a1_manager.autofocus.af_manager import AutoFocusManager
from a1_manager.autofocus.af_utils import load_config_file, save_config_file,prompt_autofocus, RestartAutofocus, QuitAutofocus
from a1_manager.utils.utility_classes import StageCoord, WellCircleCoord, WellSquareCoord


logger = logging.getLogger(__name__)

FOCUS_RANGES = {
    'ZDrive': {'large': {'searchRange': 1000, 'step': 100},
               'small': {'searchRange':  200, 'step':  10},},
    'PFSOffset': {'large': {'searchRange': 4000, 'step': 300},
                  'small': {'searchRange': 1000, 'step': 100},}}

AF_PROMPT = (
    "\nIf focus is good press Enter, else type 'r' to restart or 'q' to quit: ")



def run_autofocus(method: str, 
                  a1_manager: A1Manager, 
                  calib_path: Path, 
                  overwrite: bool, 
                  af_savedir: Path=None
                  )-> None:
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
        """
        
        # Initialize focus device
        focus_device = a1_manager.core.get_property('Core', 'Focus')
        logger.info(f'\nAutofocus with {focus_device} using {method} method')
        a1_manager.nikon.select_focus_device(focus_device)
        
        # Load dish measurements
        dish_measurements: dict[str, WellCircleCoord | WellSquareCoord] = load_config_file(calib_path)
        autofocus = AutoFocusManager(a1_manager, method, af_savedir) 
        
        for idx, (well, measurement) in enumerate(dish_measurements.items()):
            logger.info(f'\nAutofocus for well {well}')
            
            if measurement[focus_device] is not None and not overwrite:
                logger.info(f"Autofocus already done for {well} with {focus_device} at {measurement[focus_device]}")
                continue
        
            try:
                # Process the well for autofocus
                focus = _focus_one_well(idx=idx,
                                        measurement=measurement,
                                        focus_device=focus_device,
                                        autofocus=autofocus,
                                        method=method
                                        )
                    
            except QuitAutofocus:
                # Quit the autofocus process
                logger.warning("User quit; exiting without further changes.")
                return
            
            # Update dish measurements  
            measurement[focus_device] = focus
                
            # Save dish measurements and exit
            save_config_file(calib_path, dish_measurements)
            
            # success! move on to the next well
            logger.info(f"Autofocus done for {well} with {focus_device} at {focus}")
            

def _focus_one_well(*,
                    idx: int, 
                    measurement: WellCircleCoord | WellSquareCoord,
                    focus_device: str, 
                    autofocus: AutoFocusManager,
                    method: str, 
                    ) -> float:
    """
    Process a single well for autofocus.
    Args:
        idx (int): Index of the well in the list of wells.
        measurement (WellCircleCoord | WellSquareCoord): Measurement data for the well.
        focus_device (str): Focus device to use. Choose from 'ZDrive' or 'PFSOffset'.
        autofocus (AutoFocusManager): AutoFocusManager object.
        method (str): Autofocus method to use. Choose from 'sq_grad', 'OughtaFocus', 'Manual'.
    Returns:
        float: Focus value for the well.
    """
    while True:
        try:
            # Extract manager back
            a1_manager = autofocus.a1_manager
            
            # Move to center of well
            point_center = StageCoord(xy=measurement['center'])
            a1_manager.nikon.set_stage_position(point_center)
            
            # If first well, apply large focus range only for square gradient method
            if idx == 0 and method != 'Manual':
                logger.info(f'Apply large focus range for {focus_device} in the center of well')
                autofocus.find_focus(**FOCUS_RANGES[focus_device]['large'])
                    
            # Apply fine focus range
            logger.info(f'Fine tuned autofocus with {focus_device} in the center of well')
            focus = autofocus.find_focus(**FOCUS_RANGES[focus_device]['small'])
            logger.info(f'Focus value: {focus}')
                    
            # If first well, show the image
            # TODO: insert a small gui that will take care of the prompt and response
            if idx == 0:
                img = a1_manager.snap_image()
                plt.imshow(img)
                plt.show()
                prompt_autofocus(AF_PROMPT)
            return focus
        
        except RestartAutofocus:
            # loop back and retry
            logger.info("   ↻ Restarting this well…")
            
        except QuitAutofocus:
            logger.warning("   ✗ Quit detected in helper; propagating")
            raise QuitAutofocus
