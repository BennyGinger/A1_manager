from a1_manager import A1Manager, StageCoord
from tifffile import imwrite
from pathlib import Path
from a1_manager.microscope_hardware.nanopick.masterclass import WayofWater
import json
from typing import Any
from time import sleep

if __name__ == "__main__":
    
    captain = WayofWater(dish_name = '96well', injection_volume_ul = 10)
    captain.initialize_environment(injection_device = 'quickpick', needle_size = 50, pressure=0.3)

    run_dir = Path(r"D:\Ben\20251104_test_valves") 
    #well_selection = None # FIXME: All or None?
    #well_selection_test = ['A1', 'A2', 'A3']

    dish_calib_path = Path(r"C:\repos\A1_manager\config\calib_96well.json")
    with open(dish_calib_path, 'r') as f:
        dish_calib: dict[str, dict[str, Any]]= json.load(f)
    keys = list(dish_calib.keys())
    print("Wells in calibration:", keys)
    
    for well in list(keys[0:10]):
        
        captain.arm_to_home() # Lift up the head just above the plate 
        mst = dish_calib.get(well, {})
        position = StageCoord(xy=mst['center'])
        captain.a1_manager.set_stage_position(position)
        sleep(1)
        
        # Image before stimulation
        #img = a1_manager.snap_image()
        #img_name = f"{well}_before.tif"
        #imwrite(run_dir / img_name, img, compression='zlib')
        
        # Injection of ligands
        captain.arm_to_liquid()
        captain.carrier.injecting(inject_vol_ul=10)
        captain.arm_to_home()
        # sleep(1)
    
        # Image after stimulation
        #img = a1_manager.snap_image()
        #img_name = f"{well}_after.tif"
        #imwrite(run_dir / img_name, img, compression='zlib')



    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    """
            # FIXME: DO I NEED AUTOFOCUS?
        run_autofocus(method='sq_grad',
                  a1_manager=a1_manager,
                calib_path=dish_calib_path,
                well_selection=well_selection,
                overwrite=True,
        )   
    """
