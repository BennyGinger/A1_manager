from __future__ import annotations # Enable type annotation to be stored as string
import logging
from dataclasses import dataclass
from a1_manager.microscope_hardware.nanopick.marZ_api import MarZ
from a1_manager import A1Manager





# Set up logging
logger = logging.getLogger(__name__)

# initialize arm always and create a condition for the head or the valves to initialize - so it will be a condition inside this class which will get as a parameter

class InjectionManager():
    "Class to control the injection depending on the chosen device: nanopick head or quicpick valve control."
    __slots__ = 'a1_manager', 'arm', 'device'
    self.a1_manager = A1Manager()
    
    def __init__(self, injection_device: str = None, volume: float, time: int | None = None, nanopick_dish: str): # type: ignore
        """
            Possible device names:
            - 'nanopick'
            - 'quickpick'
        """

        self.injection_time = time
        self.injection_volume = volume
 
        if injection_device is None:
            self.arm = MarZ(self.core, nanopick_dish) # type: ignore
        if injection_device is not None:
            if injection_device == "nanopick":
                from a1_manager.microscope_hardware.nanopick.head_api import Head
                self.device = Head(self.arm)
            if injection_device == "quickpick":
                from a1_manager.microscope_hardware.nanopick.valves import PICController
                # FIXME: pressure and needle size input!
                self.device =  PICController(needle_size = needle_size, pressure=pressure)
                
     def mini_injection_pipeline(nanopick_dish: str = nanopick_dish,  needle_size = int, pressure = float):
         import json
         from pathlib import Path
         from time import sleep
         from typing import Any
         from a1_manager import StageCoord

         run_dir = Path(r"D:\Ben\20251104_test_valves") 

         
         if nanopick_dish = '96well':
            dish_calib_path = Path(r"C:\repos\A1_manager\config\calib_96well.json")
            with open(dish_calib_path, 'r') as f:
            dish_calib: dict[str, dict[str, Any]]= json.load(f)
            keys = list(dish_calib.keys())
   
         for well in list(keys):
       
             arm.to_home() # Lift up the head above the plate
             mt = dish_calib.get(well, {})
             position = StageCoord(xy=mt['center'])
             self.a1_manager.set_stage_position(position)
             sleep(1)

             # Image before stimulation
             img = a1_manager.snap_image()
             img_name = f"{well}_before.tif"
             imwrite(run_dir / img_name, img, compression='zlib')
        
           
             # Injection of ligands
             
             device.injecting(inject_vol_ul=self.injection_volume, mixing_cycles=6)
             arm.to_liquid()
             arm.to_home()
             sleep(1)


            # Image after stimulation
            img = a1_manager.snap_image()
            img_name = f"{well}_after.tif"
            imwrite(run_dir / img_name, img, compression='zlib')


     def mini_diffusion_pipeline(nanopick_dish: str,  ):
   
 
            
# Example usage
if __name__ == "__main__":
     import time
     import json
     from pathlib import Path
     from time import sleep
     from typing import Any
     from a1_manager import StageCoord

     master = InjectionManager(nanopick_dish = '96well', injection_device = 'quickpick', needle_size = 70, pressure=0.2)


    

    


    

     
     
     
     
     

            
