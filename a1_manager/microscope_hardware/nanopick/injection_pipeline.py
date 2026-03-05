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
        
    
        master = Injection(dish_name = "96well", injection_volume_ul = 10, injection_time_ms = None)   
        injection_device = master.get_injection_device(injection_device = 'quickpick', needle_size = 50, pressure=0.3) 
        a1_manager = A1Manager(objective = '10x', lamp_name = 'pE-800') # type: ignore
        
        run_dir = Path('D:\\Zsuzsi\\inj_pipeline_test')
        well_selection = "all"  # Choose the well to stimulate
        a1_manager.oc_settings('GFP')

        grids = launch_dish_workflow(
        a1_manager=a1_manager,
        run_dir=run_dir,
        dish_name="96well",
        af_method='Manual',
        well_selection= well_selection,
        dmd_window_only=False,
        numb_field_view=None,)

        # dish_calib = {}
        # keys = []

        dish_calib_path = Path(r"C:\Users\uManager\Documents\__repos__\GEM_suite\A1_manager\config\calib_96well.json")
        with open(dish_calib_path, 'r') as f:
                dish_calib: dict[str, dict[str, Any]]= json.load(f)
                keys = list(dish_calib.keys())
   
        for well, grid in grids.items():
       
             master.arm_to_home() # Lift up the arm above the plate
             a1_manager.oc_settings('GFP')
             print(f"Imaging before injection for well {well}...")
             
             for ind, point in grid.items():
                a1_manager.set_stage_position(point)
                img = a1_manager.snap_image()
                img_name = f"before_{well}P{ind}.tif"
                imwrite(run_dir / img_name, img)
                print(f"Saved image {img_name} at {run_dir / img_name}")
            
             # Move to the center of the well based on the calibration data
             mt = dish_calib.get(well, {})
             position = master.position_converter(position=mt['center'])
             a1_manager.set_stage_position(position)
             img = a1_manager.snap_image()
             img_name = f"InjectionBefore_{well}.tif"
             imwrite(run_dir / img_name, img, compression='zlib')
             
             # Injection of ligands
             injection_device.inject(master.injection_volume_ul, mixing_cycles=3)
             #master.arm_to_liquid() # Dip it in the liquid because of the drops.
             master.arm_to_home()
             sleep(1)
             
             img = a1_manager.snap_image()
             img_name = f"InjectionAfter_{well}.tif"
             imwrite(run_dir / img_name, img, compression='zlib')
             
             a1_manager.oc_settings('GFP')
             
             for ind, point in grid.items():
                a1_manager.set_stage_position(point)
                img = a1_manager.snap_image()
                img_name = f"inj_after_{well}P{ind}.tif"
                imwrite(run_dir / img_name, img, compression='zlib')
             