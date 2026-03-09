from __future__ import annotations # Enable type annotation to be stored as string
import logging

import json
from pathlib import Path
from tifffile import imwrite
from time import sleep
from typing import Any

from a1_manager.microscope_hardware.nanopick.injection_factory import Injection
from a1_manager import A1Manager, launch_dish_workflow


# Set up logging
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    
        """
        Automated stimulation protocol using the valve system. 
        
        """     
        import json
        from pathlib import Path
        from tifffile import imwrite
        from typing import Any

        master = Injection(injection_device = 'quickpick', dish_name = "96well", needle_size = 50, pressure=0.3)   
        a1_manager = A1Manager(objective = '20x', lamp_name = 'pE-800', focus_device  = 'PFSOffset') # type: ignore
        
        run_dir = Path('D:\\Zsuzsi\\inj_pipeline_test\\20260312_injection_test') # Set the directory where the images will be saved
        well_selection = "all" #['F1','F2','F3','F4','F5','F6','F7','F8','F9','F10','F11','F12']  # Choose the well to stimulate

        grids = launch_dish_workflow(
        a1_manager=a1_manager,
        run_dir=run_dir,
        dish_name="96well",
        af_method='Manual',
        well_selection= well_selection,
        dmd_window_only=False,
        numb_field_view=None,)

        dish_calib = {}
        keys = []

        # Load the dish calibration data to get the center position of the wells for washing effect monitoring
        dish_calib_path = Path(r"C:\Users\uManager\Documents\__repos__\GEM_suite\A1_manager\config\calib_96well.json")
        with open(dish_calib_path, 'r') as f:
                dish_calib: dict[str, dict[str, Any]]= json.load(f)
                keys = list(dish_calib.keys())
   
        for well, grid in grids.items():
       
             master.arm_to_home() # Lift the arm above the plate
             a1_manager.oc_settings('GFP')
             print(f"Imaging {well}...")
             
             # Screening before: Take images from the grid positions before injection
             for ind, point in grid.items():
                a1_manager.set_stage_position(point)
                img = a1_manager.snap_image()
                img_name = f"baseline_{well}P{ind}.tif"
                imwrite(run_dir / img_name, img)
                print(f"Saved image {img_name}")
            
             # Move to the center of the well based on the calibration data
             mt = dish_calib.get(well, {})
             position = master.position_converter(position=mt['center'])
             a1_manager.set_stage_position(position)
             print(f"Moved to the center of well {well} at position {position}.")
            
             # Take an image from the center before injection
             img = a1_manager.snap_image()
             img_name = f"InjectionBefore_{well}.tif"
             imwrite(run_dir / img_name, img, compression='zlib')
             print(f"Saved image {img_name}")
             
             # Inject the substance using the valve system
             master.inject(inject_vol_ul=10, mixing_cycles=3)
             
             # Take an image from the center after injection
             img = a1_manager.snap_image()
             img_name = f"InjectionAfter_{well}.tif"
             imwrite(run_dir / img_name, img, compression='zlib')
             print(f"Saved image {img_name}")
             
             a1_manager.oc_settings('GFP')
             
             # Screening after: Take images from the grid positions after injection
             for ind, point in grid.items():
                a1_manager.set_stage_position(point)
                img = a1_manager.snap_image()
                img_name = f"stimulated_{well}P{ind}.tif"
                imwrite(run_dir / img_name, img, compression='zlib')
                print(f"Saved image {img_name}")
                
                
                
                
        