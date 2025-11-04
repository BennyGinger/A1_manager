from a1_manager import A1Manager, StageCoord, launch_dish_workflow
import numpy as np


def fov_stimulate(data: dict, pattern: str):  
    x = [] 
    y = []   
    for _, coord in data.items():
        x.append(coord["xy"][0])
        y.append(coord["xy"][1])
    if pattern == "3x3":
        fov_1 = [7, 6, 5, 11, 20, 21, 22, 9, 10] # upper left
        fov_2 = [37, 36, 35, 51, 52, 53, 54, 49, 50] # (quite) in the middle 
        fov_3 = [27, 28, 29, 38, 48, 47, 46, 40, 39] # lower right
        fov1 = []
        for i in range(len(fov_1)):
            fov1.append([x[fov_1[i]], y[fov_1[i]]])
        fov2 = []
        for i in range(len(fov_2)):
            fov2.append([x[fov_2[i]], y[fov_2[i]]])
        fov3 = []
        for i in range(len(fov_3)):
            fov3.append([x[fov_3[i]], y[fov_3[i]]])
        return fov1, fov2, fov3


    if pattern == "5x5":
        # 5*5 fov
        fov_5_5 = [8, 9, 10, 11, 12, 19, 29, 38, 48, 47, 46, 45, 44, 42, 25, 23, 22, 21, 20, 28, 39, 40, 41, 26, 27]
        fov5 = []
        for i in range(len(fov_5_5)):
                  fov5.append([x[fov_5_5[i]], y[fov_5_5[i]]])
        fov_3 = [27, 28, 29, 38, 48, 47, 46, 40, 39] # lower right
        fov3 = []
        for i in range(len(fov_3)):
                 fov3.append([x[fov_3[i]], y[fov_3[i]]])
        return fov3, fov5
    

if __name__ == "__main__":
    from tifffile import imwrite 
    from pathlib import Path
    import json
    from typing import Any
    
    run_dir = Path(r"D:\Ben\20251104_test_valves")        
    well_selection = "B1"  # Choose the well to stimulate
    focus_value = 15000  # Set the focus value for the selected well
    subgrid_instance = 0
    dish_name = '96well'
    
    a1_manager = A1Manager(
        objective='20x',
        lamp_name='pE-800',
        focus_device='PFSOffset',
        nanopick_dish=dish_name,
        injection_device='quickpick')
    
    grid = launch_dish_workflow(
        a1_manager=a1_manager,
        run_dir=run_dir,
        dish_name=dish_name,
        well_selection=well_selection,
        af_method='Manual',
        dmd_window_only=False,
        numb_field_view=None,)
    
    dish_calib_path = Path(r"C:\repos\A1_manager\config\calib_96well.json")
    with open(dish_calib_path, 'r') as f:
        dish_calib: dict[str, dict[str, Any]]= json.load(f)
    
    # prepare the subgrid to stimulate
    subgrid_lst = fov_stimulate(grid[well_selection], "3x3")
    
    a1_manager.injection.attachment.set_valve_time(1, 100)
    a1_manager.injection.attachment.set_valve_time(2, 100) 
    a1_manager.injection.attachment.set_delay(10)
    
    for i, xy_coords in enumerate(subgrid_lst[subgrid_instance]):
        a1_manager.injection.arm.to_air()
         
        stage_coord = StageCoord()
        setattr(stage_coord, 'xy', xy_coords)
        setattr(stage_coord, 'PFSOffset', focus_value)
        
        a1_manager.injection.arm.safe_check()
        a1_manager.set_stage_position(stage_coord)
        img = a1_manager.snap_image()
        img_name = f"{i}_round1.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        
        # Inject
        a1_manager.injection.arm.to_liquid()
        a1_manager.injection.attachment.injecting(volume=10, time=100)
        a1_manager.injection.arm.to_air()
        
    for i, xy_coords in enumerate(subgrid_lst[subgrid_instance][::-1]):
        stage_coord = StageCoord()
        setattr(stage_coord, 'xy', xy_coords)
        setattr(stage_coord, 'PFSOffset', focus_value)
        
        a1_manager.injection.arm.safe_check()
        a1_manager.set_stage_position(stage_coord)
        
        img = a1_manager.snap_image()
        img_name = f"{i}_round2.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
    

    

    # TODO: Scan only the edge points, not the whole thing
    