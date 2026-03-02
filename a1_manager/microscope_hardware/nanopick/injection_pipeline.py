from __future__ import annotations # Enable type annotation to be stored as string
import logging

import json
from pathlib import Path
from tifffile import imwrite
from time import sleep
from typing import Any

from a1_manager.microscope_hardware.nanopick.devices.marZ import MarZ
from a1_manager.microscope_hardware.nanopick.devices.injection_device import Init_Device
from a1_manager.microscope_hardware.nanopick.injection_factory import Inject
from a1_manager import A1Manager

# Set up logging
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    
        """
        Automated stimulation protocol using the valve system. 
        
        """
        arm = MarZ(core=a1_manage.core, dish='96well')
        injection_device = Init_Device(injection_device = 'quickpick') 
        injection_device.set_quick_params(needle_size = 50, pressure = 0.2)
        a1_manager = A1Manager(objective = '10x', lamp_name = 'pE-800')
        master = Inject(arm = arm, injection_device = injection_device, a1_manager = a1_manager)

        run_dir = Path('D:\\Zsuzsi\\inj_pipeline_test')
        dish_calib = {}
        keys = []

        dish_calib_path = Path(r"C:\Users\uManager\Documents\__repos__\GEM_suite\A1_manager\config\calib_96well.json")
        with open(dish_calib_path, 'r') as f:
                dish_calib: dict[str, dict[str, Any]]= json.load(f)
                keys = list(dish_calib.keys())
   
        for well in list(keys):
       
             master.arm_to_home() # Lift up the arm above the plate
             mt = dish_calib.get(well, {})
             position = master.position_converter(position=mt['center'])
             a1_manager.set_stage_position(position)
             sleep(1)

             # Image before stimulation
             img = a1_manager.snap_image()
             img_name = f"{well}_before.tif"
             imwrite(run_dir / img_name, img, compression='zlib')
        
             # Injection of ligands
             master.injection_device.inject(10)
             master.arm_to_liquid() # Dip it in the liquid because of the drops.
             master.arm_to_home()
             sleep(1)

             # Image after stimulation
             img = a1_manager.snap_image()
             img_name = f"{well}_after.tif"
             imwrite(run_dir / img_name, img, compression='zlib')  
