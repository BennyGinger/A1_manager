from a1_manager import A1Manager, StageCoord, launch_dish_workflow
import numpy as np


def fov_stimulate(self, data: dict, pattern: str) -> tuple[list, list, list]:  
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
    from a1_manager.utils.utils import load_json
    
    run_dir = Path(r"D:\Ben\20251017_test_nanopick")        
    well_selection = "B1"  # Choose the well to stimulate
    focus_valuse = 15000  # Set the focus value for the selected well
    subgrid_instance = 0
    well_filling = 'A1'
    well_waste = 'A2'
    
    
    a1_manager = A1Manager(
        objective='20x',
        lamp_name='pE-800',
        focus_device='PFSOffset',
        nanopick_dish='96well',)
    
    grid = launch_dish_workflow(
        a1_manager=a1_manager,
        run_dir=run_dir,
        dish_name='96well',
        well_selection=well_selection,
        af_method='Manual',
        dmd_window_only=False,
        numb_field_view=None,)
    
    calib = load_json(run_dir.joinpath('config', 'calib_96well.json'))
    
    # Fill the pipette with ligand
    waste_coord = calib[well_waste]["center"]
    wc = StageCoord()
    wc = setattr(wc, 'xy', waste_coord)
    a1_manager.set_stage_position(wc)
    a1_manager.injecting(volume=500)
    
    filling_coord = calib[well_filling]["center"]
    fc = StageCoord()
    fc = setattr(fc, 'xy', filling_coord)
    a1_manager.set_stage_position(fc)
    a1_manager.filling(volume=500)

    # prepare the subgrid to stimulate
    subgrid_lst = fov_stimulate(grid[well_selection], "3x3")
    
    for i, xy_coords in enumerate(subgrid_lst[subgrid_instance]):
        stage_coord = StageCoord()
        stage_coord = setattr(stage_coord, 'xy', xy_coords)
        stage_coord = setattr(stage_coord, 'PFSOffset', focus_valuse)
        a1_manager.set_stage_position(stage_coord)
        img = a1_manager.snap_image()
        img_name = f"{i}_round1.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        
        # Inject
        a1_manager.injecting(volume=500)
        a1_manager.set_stage_position(fc)
        a1_manager.filling(volume=500)
        
    for i, xy_coords in enumerate(subgrid_lst[subgrid_instance][::-1]):
        stage_coord = StageCoord()
        stage_coord = setattr(stage_coord, 'xy', xy_coords)
        stage_coord = setattr(stage_coord, 'PFSOffset', focus_valuse)
        a1_manager.set_stage_position(stage_coord)
        img = a1_manager.snap_image()
        img_name = f"{i}_round2.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

    #     fov_5_5_center = [x[center_5_5], y[center_5_5]]
    #     fov_5_5_ctr = data[well][str(center_5_5)]["xy"]




    #     all_index = list(np.arange(68))  
    #     indexes = [5, 6, 7, 9, 10, 11, 20, 21, 22, 27, 28, 29, 38, 39, 40, 46, 47, 48, 35, 36, 37, 49, 50, 51, 52, 53, 54]
    #     # Eliminate the coodinates of 3*3 fovs from all indexes
    #     for index in sorted(indexes, reverse=True):
    #         del all_index[index]

    #     all_index_5_5 = list(np.arange(68)) 
    #     indexes_5_5 = fov_5_5 + fov_3
    #     # Eliminate the coodinates of 5*5 and one 3*3 fov from all indexes
    #     for index in sorted(indexes_5_5, reverse=True):
    #         del all_index_5_5[index]
        
    
    

