from __future__ import annotations # Enable type annotation to be stored as string
import logging
from a1_manager.microscope_hardware.nanopick.devices.marZ import MarZ
from a1_manager import A1Manager
from a1_manager import StageCoord

import json
from pathlib import Path
from tifffile import imwrite
from time import sleep
from typing import Any


# Set up logging
logger = logging.getLogger(__name__)

class WayofWater():
    """ 
    Class to control the injection depending on the chosen device: nanopick head or quickpick valve control.
    Args:
        - injection_volume(float): injected volume in microliters
        - injection_time(int): injection time in milliseconds
        - nanopick_dish(str): name of the used dish (e.g.: "96-well")
    """
    
    __slots__ = 'a1_manager', 'arm', 'carrier', 'injection_time_ms', 'injection_volume_ul', 'dish_name'
    
    def __init__(self,  dish_name: str, injection_volume_ul: float, injection_time_ms: int | None = 100 ): # type: ignore
        
        self.a1_manager = A1Manager(objective = '10x', lamp_name = 'pE-800')
        self.arm = MarZ(self.a1_manager.core, dish_name) # type: ignore
        self.injection_time_ms = injection_time_ms    # in milliseconds
        self.injection_volume_ul = injection_volume_ul # in microliters
        self.dish_name = dish_name
    
    def position_converter(self, position: tuple[float, float]) -> StageCoord:
        """ 
        Convert position from tuple to StageCoord.
        """
        return StageCoord(position)
    
    def _ul_to_nl_converter(self, volume_ul: float) -> float:
        """
        Convert volume from microliters to nanoliters.
        """
        return volume_ul*1000
    
    def arm_to_home(self)->None:
        """
        Move to the safe height above the plate.
        """
        return self.arm.to_home()
    
    def arm_to_liquid(self)->None:
        """
        Move to the position in the liquid safely above the cells.
        """
        return self.arm.to_liquid()
        
    def get_arm_position(self)-> float:
        """
        Get the current altitude of the head.
        """
        return self.arm._get_arm_position
        
    def initialize_environment(self, injection_device: str, needle_size: int | None = None, pressure: float | None = None):
        """ 
        Initialize the injection device. 

        Args:
            - injection_device(str): possible device names -> 'nanopick', 'quickpick'
            - needle_size(int): for valves, possible values -> 30, 50, 70 um
            - pressure(float): for valves, possible values -> [0,6] bar - for the 50 um needle size: 0.2, 0.3, 0.4 bar
        """
        if injection_device == "nanopick":
            from a1_manager.microscope_hardware.nanopick.devices.head import Head
            self.carrier = Head()
            
        if injection_device == "quickpick":
            if needle_size == None or pressure == None:
                    logger.error("Needle size and pressure value is needed for using the valve system.")
            else:
                    from a1_manager.microscope_hardware.nanopick.devices.valve import PICController
                    self.carrier =  PICController(needle_size = needle_size, pressure=pressure, test_mode= True)
                    
    def fill_head(self, fill_vol_ul: float, fill_time_ms: float = 100) -> None:
        """ 
        Filling using the head system.

        Args:
            - fill_vol_ul(float): filling volume in microliters
            - fill_time_ms(float): filling time in milliseconds (default: 100 ms)
        """
        if self.carrier == "quickpick":
            logger.error("Filling is not possible with the valve system.")  
            
        if self.carrier == "nanopick":
            fill_vol_ul = self._ul_to_nl_converter(fill_vol_ul)
            self.carrier.filling(fill_vol_ul, fill_time_ms)  # type: ignore
                    
                    
    def inject(self, inject_vol_ul: float, inject_time_ms: float | None = None, mixing_cycles: int = 1):
        """ 
        Injection using the valve system.

        Args:
            - inject_vol_ul(float): injection volume in microliters
            - inject_time_ms(float): injection time in milliseconds, will be None in case of valves
            - mixing_cycles(int): number of mixing cycles (default: 1)
        """
        if self.carrier == "nanopick":
            inject_vol_ul = self._ul_to_nl_converter(inject_vol_ul)
            
        self.carrier.inject(inject_vol_ul, inject_time_ms, mixing_cycles)
                    
    def mini_injection_pipeline(self, run_dir: Path):
        """
        Automated stimulation protocol using the valve system. 
        
        """
         
        run_dir = run_dir
        dish_calib = {}
        keys = []
         
        if self.dish_name == '96well':
            dish_calib_path = Path(r"C:\Users\uManager\Documents\__repos__\GEM_suite\A1_manager\config\calib_96well.json")
            with open(dish_calib_path, 'r') as f:
                dish_calib: dict[str, dict[str, Any]]= json.load(f)
                keys = list(dish_calib.keys())
   
        for well in list(keys):
       
             self.arm_to_home() # Lift up the arm above the plate
             mt = dish_calib.get(well, {})
             position = self.position_converter(position=mt['center'])
             self.a1_manager.set_stage_position(position)
             sleep(1)

             # Image before stimulation
             img = self.a1_manager.snap_image()
             img_name = f"{well}_before.tif"
             imwrite(run_dir / img_name, img, compression='zlib')
        
             # Injection of ligands
             self.carrier.inject(self.injection_volume_ul)
             self.arm_to_liquid() # Dip it in the liquid because of the drops.
             self.arm_to_home()
             sleep(1)

             # Image after stimulation
             img = self.a1_manager.snap_image()
             img_name = f"{well}_after.tif"
             imwrite(run_dir / img_name, img, compression='zlib')


    def mini_diffusion_pipeline(self, run_dir: Path):
        """
         Diffusion stimulation protocol using the head. 
         
        """

        run_dir = run_dir
        dish_calib = {} 
        keys = []
         
        if self.dish_name == '96well':
            dish_calib_path = Path(r"C:\Users\uManager\Documents\__repos__\GEM_suite\A1_manager\config\calib_96well.json")
            with open(dish_calib_path, 'r') as f:
                dish_calib: dict[str, dict[str, Any]]= json.load(f)
                keys = list(dish_calib.keys())
        
        filling_wells = keys[0:12]
        injection_wells = keys[12:]   
            
        for i in range(len(injection_wells)):
                
                self.arm_to_home() # Lift up the arm above the plate
                mt = dish_calib.get(injection_wells[i], {})
                position = self.position_converter(position=mt['center'])
                self.a1_manager.set_stage_position(position)
                sleep(1)
                
                # Image before stimulation
                img = self.a1_manager.snap_image()
                img_name = f"{injection_wells[i]}_before.tif"
                imwrite(run_dir / img_name, img, compression='zlib')
                
                # Move down the arm to reach the liquid
                self.carrier.switch_LED_on() # type: ignore
                self.arm_to_liquid()

                # Injection from the head
                if self.injection_time_ms is not None:
                    self.carrier.inject(self.injection_volume_ul, self.injection_time_ms)
                else:
                    self.carrier.inject(self.injection_volume_ul)

                # Move up the head
                self.arm_to_home()
                self.carrier.switch_LED_off() # type: ignore
                
                # Image after stimulation
                img = self.a1_manager.snap_image()
                img_name = f"{injection_wells[i]}_after.tif"
                imwrite(run_dir / img_name, img, compression='zlib')

                # Fill the head after every row
                if i % 11 == 0: 
                    # Move up the head
                    self.arm_to_home()
                    filling_well_index = (i // 11) -1
        
                    # Go to filling station
                    mt = dish_calib.get(filling_wells[filling_well_index], {})
                    position = self.position_converter(position=mt['center'])
                    self.a1_manager.set_stage_position(position)
        
                    # Move down the head to reach the liquid
                    self.carrier.switch_LED_on() # type: ignore
                    self.arm_to_liquid()

                    # Fill the head
                    #FIXME: this value needs to be calibrated
                    self.fill_head(400) # type: ignore  # 400 nl in 100 ms
            
                    # Move up the head
                    self.arm_to_home()
                    self.carrier.switch_LED_off() # type: ignore
            
if __name__ == "__main__":

    ### Initialization of the valve system
    
    captain = WayofWater(dish_name = '96well', injection_volume_ul = 10)
    
    # Needle size and pressure is needed for valve system
    captain.initialize_environment(injection_device = 'quickpick', needle_size = 50, pressure=0.3)
    
    #For calibration of the valve system
    for i in range(1):
        print(f"Instance {i+1}")
        captain.carrier.inject(inject_vol_ul=1740) 
         
    # Run stimulation pipeline     
    # run_dir = Path('D:\\Zsuzsi\\test_lib')
    # captain.mini_injection_pipeline(run_dir=run_dir)
    
    
    
    
    # ## Initialization of the head (nanopick)
    
    # captain = WayofWater(dish_name = '96well', injection_volume_ul = 10, injection_time_ms = 100)
    # captain.initialize_environment(injection_device = 'nanopick')
    
    # run_dir = Path('D:\\Zsuzsi\\test_lib')
    # captain.mini_diffusion_pipeline(run_dir=run_dir)

     

