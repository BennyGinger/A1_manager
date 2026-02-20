from __future__ import annotations # Enable type annotation to be stored as string
import logging

import json
from pathlib import Path
from tifffile import imwrite
import time
from typing import Any

from a1_manager.microscope_hardware.nanopick.injection_factory import Injection
from a1_manager import A1Manager

# Set up logging
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    
    master = Injection(dish_name = "96-well", injection_volume_ul = 10, injection_time_ms = None)   
    injection_device = master.get_injection_device(injection_device = 'quickpick', needle_size = 50, pressure=0.2) 
    a1_manager = A1Manager(objective = '10x', lamp_name = 'pE-800')


    save_dir = Path(r"C:\Users\uManager\Desktop\test\sixth")
    a1_manager = A1Manager(objective='20x', lamp_name='pE-800')
    a1_manager.oc_settings(optical_configuration='GFP')
    for i in range(13):
        print(f"Cycle {i}")
        
        # channel 1
        a1_manager.oc_settings(optical_configuration='GFP')
        if i==0:
            a1_manager.snap_image()
            time.sleep(3)
        img = a1_manager.snap_image()
        imwrite(save_dir / f"GFP_{i}.tif", img)
        
        # channel 2
        a1_manager.oc_settings(optical_configuration='405GFP')
        if i==0:
            a1_manager.snap_image()
            time.sleep(1)
        img2 = a1_manager.snap_image()
        imwrite(save_dir / f"405_{i}.tif", img2)
        
        # Manual injection at cycle 5
        if i == 5:
            print("Injecting...")
            
        # Automated injection *(*uncomment if you want to test the injection, make sure to have the injection device set up and calibrated properly)*
        # if i == 5:
        #     print("Injecting...")
        #     injection_device.inject(master.injection_volume_ul, mixing_cycles=3)
            
        time.sleep(10)
    