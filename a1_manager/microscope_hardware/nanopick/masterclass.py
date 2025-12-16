from __future__ import annotations # Enable type annotation to be stored as string
import logging
from a1_manager.microscope_hardware.nanopick.marZ_api import MarZ
from a1_manager import A1Manager
from a1_manager import StageCoord


# Set up logging
logger = logging.getLogger(__name__)


class InjectionManager():
    """ 
    Class to control the injection depending on the chosen device: nanopick head or quicpick valve control.
    Args:
        - injection_volume(float): injected volume in microliters
        - injection_time(int): injection time in milliseconds
        - nanopick_dish(str): name of the used dish (e.g.: "96-well")
    """
    
    __slots__ = 'a1_manager', 'arm', 'device', 'injection_time', 'injection_volume', 'nanopick_dish'
    
    def __init__(self,  nanopick_dish: str, injection_volume: float, injection_time: int = 100 | None = None): # type: ignore
        
        self.a1_manager = A1Manager()
        self.arm = MarZ(self.core, nanopick_dish) # type: ignore
        self.injection_time = injection_time
        self.injection_volume = injection_volume
        self.nanopick_dish = nanopick_dish
    
    def _position_converter(self, position):
        return StageCoord(position)
    
    def _ul_to_nl_converter(self, volume_ul: float):
        return volume_ul*1000
        
    def initialize_pick(self, injection_device: str, needle_size: int | None = None, pressure: float | None = None):
            """
                Args:
                    - injection_device(str): possible device names -> 'nanopick', 'quickpick'
                    - needle_size(int): for valves, possible values -> 30, 50, 70 um
                    - pressure(float): for valves, possible values -> [0,6] bar
            """
            if injection_device == "nanopick":
                from a1_manager.microscope_hardware.nanopick.head_api import Head
                self.device = Head()
            if injection_device == "quickpick":
                if needle_size == None or pressure == None:
                    logger.error("Needle size and pressure value is needed for using the valve system.")
                else:
                    from a1_manager.microscope_hardware.nanopick.valves import PICController
                    self.device =  PICController(needle_size = needle_size, pressure=pressure)
                    
    def mini_injection_pipeline(self):
        """Automated stimulation protocol using the valve system. """
         import json
         from pathlib import Path
         from tifffile import imwrite
         from time import sleep
         from typing import Any
         

         run_dir = Path(r"D:\Ben\20251104_test_valves") 
         
         if self.nanopick_dish == '96well':
            dish_calib_path = Path(r"C:\repos\A1_manager\config\calib_96well.json")
            with open(dish_calib_path, 'r') as f:
                dish_calib: dict[str, dict[str, Any]]= json.load(f)
                keys = list(dish_calib.keys())
   
         for well in list(keys):
       
             self.arm.to_home() # Lift up the head above the plate
             mt = dish_calib.get(well, {})
             position = self.position_converter(xy=mt['center'])#StageCoord(xy=mt['center'])
             self.a1_manager.set_stage_position(position)
             sleep(1)

             # Image before stimulation
             img = self.a1_manager.snap_image()
             img_name = f"{well}_before.tif"
             imwrite(run_dir / img_name, img, compression='zlib')
        
           
             # Injection of ligands
             self.device.injecting(inject_vol_ul=self.injection_volume)
             self.arm.to_liquid()
             self.arm.to_home()
             sleep(1)


             # Image after stimulation
             img = self.a1_manager.snap_image()
             img_name = f"{well}_after.tif"
             imwrite(run_dir / img_name, img, compression='zlib')


    def mini_diffusion_pipeline(self):
         """Diffusion stimulation protocol using the head. """
        import json
        from pathlib import Path
        from tifffile import imwrite
        from time import sleep
        from typing import Any
        from a1_manager import StageCoord

        run_dir = Path(r"D:\Ben\20251104_test_valves") 
         
        if self.nanopick_dish == '96well':
            dish_calib_path = Path(r"C:\repos\A1_manager\config\calib_96well.json")
            with open(dish_calib_path, 'r') as f:
                dish_calib: dict[str, dict[str, Any]]= json.load(f)
                keys = list(dish_calib.keys())
        
        filling_wells = keys[0:12]
        injection_wells = keys[12:]   
            
        for i in range(len(injection_wells)):
                
                self.arm.to_home() # Lift up the head above the plate
                mt = dish_calib.get(injection_wells[i], {})
                position = self.position_converter(xy=mt['center'])
                self.a1_manager.set_stage_position(position)
                sleep(1)
                
                # Image before stimulation
                img = self.a1_manager.snap_image()
                img_name = f"{injection_wells[i]}_before.tif"
                imwrite(run_dir / img_name, img, compression='zlib')
                
                # Move down the head to reach the liquid
                self.device.switch_LED_on
                self.arm.to_liquid()

                # Injection from the head
                self.device.injection(self.ul_to_nl_converter(self.injection_volume), self.injection_time)

                # Move up the head
                self.arm.to_home()
                self.device.switch_LED_off
                
                # Image after stimulation
                img = self.a1_manager.snap_image()
                img_name = f"{injection_wells[i]}_after.tif"
                imwrite(run_dir / img_name, img, compression='zlib')

                # Fill the wells after every row
                if i % 11 == 0: 
                    # Move up the head
                    self.arm.to_home()
        
                    # Go to filling station
                    mt = dish_calib.get(filling_wells[(i/11)-1], {})
                    position = self.position_converter(xy=mt['center'])#StageCoord(xy=mt['center'])
                    self.a1_manager.set_stage_position(position)
        
                    # Move down the head to reach the liquid
                    self.device.switch_LED_on
                    self.arm.to_liquid()

                    # Fill the head
                    #FIXME: these values needs to be calibrated
                    self.device.filling(400, 100)
            
                    # Move up the head
                    self.arm.to_home()
                    self.device.switch_LED_off
                    
            
if __name__ == "__main__":

     master = InjectionManager(nanopick_dish = '96well', injection_volume = 10)
     master.initialize_pick(injection_device = 'quickpick', needle_size = 50, pressure=0.35)

     #For testing
     for i in range(100):
         print(f"Instance {i+1}")
         master.device.injecting(inject_vol_ul=10, mixing_cycles=2) 
     

