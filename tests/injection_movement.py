from a1_manager import A1Manager, StageCoord
import numpy as np
from pathlib import Path
from tifffile import imwrite
import time
import json
from typing import Any




def continuous(well, x0, y0, run_dir, offset=3000):
    # While injecting continuously we move the stage.
        a1_manager.nikon.select_focus_device('PFSOffset')
        a1_manager.oc_settings("GFP")
        # P1: top x0,y0-2450
        # P2: bottom x0,y0+2900
        # P3: right x0-2800,y0       
        # P4: left x0+2500,y0
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{3}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{2}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{4}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before_middle.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.nikon.select_focus_device('ZDrive')
        controller.inject(inject_vol_ul=10, mixing_cycles=1)
        for i in range(2):
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450])) #type: ignore
            a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0])) #type: ignore
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900])) #type: ignore
            a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0])) #type: ignore
        
        a1_manager.nikon.select_focus_device('PFSOffset')
        a1_manager.oc_settings("GFP")
# Final imaging 
        for i in range(90):
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{1}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0-2700,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{2}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{3}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{4}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final_middle_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
        
def divided(well, x0, y0, offset=3000):
        # Whe inject in four different places equal volumes, so the sum is 10 ul.
        run_dir = Path('D:\\Zsuzsi\\20260512_injection_movement_test\\Divided\\E2')
        a1_manager.nikon.select_focus_device('PFSOffset')
        a1_manager.oc_settings("GFP")
        
    
        # Before imaging
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{2}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{3}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{4}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before_middle.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        
        # Injection at four different sites - here ther is not enogh time for that
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450])) #type: ignore
        controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
        time.sleep(1) # wait a bit for the injection to finish, adjust as needed
        a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0])) #type: ignore
        controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
        time.sleep(1) # wait a bit for the injection to finish, adjust as needed
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900])) #type: ignore
        controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
        time.sleep(1) # wait a bit for the injection to finish, adjust as needed
        a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0])) #type: ignore
        controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
        time.sleep(1) # wait a bit for the injection to finish, adjust as needed
        
        #time.sleep(5) # wait a bit for the injection to finish, adjust as needed
         
        # After imaging 
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_after{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_after{2}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_after{3}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_after{4}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_after_middle.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}") 
            
def integrated_imaging_with_pfs(well, x0, y0, run_dir, pfs_offset):
        # We inject in four different places equal volumes, so the sum is 10 ul - iamging before and after in the place of injection and in the middle of the well.
    
        
        a1_manager.nikon.select_focus_device('PFSOffset')
        a1_manager.oc_settings("GFP")
        
        for i in range(1):
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_previous{1}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_previous{2}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_previous{3}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_previous{4}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_previous_middle_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2000], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_baseline{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0-2000,y0], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_baseline{2}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2000], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_baseline{3}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0+2000,y0], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_baseline{4}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_baseline_middle.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
    
        start = time.time()
        # Before injection
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2000], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        arm.to_liquid()
        
        controller.inject(inject_vol_ul=5, mixing_cycles=1)
        
        arm.to_home()
        
        time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        img = a1_manager.snap_image()
        img_name = f"{well}_after{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        
        # # Middle 1
        # a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
        # img = a1_manager.snap_image()
        # img_name = f"{well}_middle{1}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        
        
        # a1_manager.set_stage_position(StageCoord(xy=[x0-2000,y0], PFSOffset=pfs_offset)) #type: ignore
        # img = a1_manager.snap_image()
        # img_name = f"{well}_before{2}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        # time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        # arm.to_liquid()
        
        # controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
        
        # arm.to_home()
        
        # time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        # img = a1_manager.snap_image()
        # img_name = f"{well}_after{2}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        # a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
        # img = a1_manager.snap_image()
        # img_name = f"{well}_middle{2}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        
        # a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2000], PFSOffset=pfs_offset))  #type: ignore
        # img = a1_manager.snap_image()
        # img_name = f"{well}_before{3}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        # time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        # arm.to_liquid()
        
        # controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
        
        # arm.to_home()
        
        # time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        # img = a1_manager.snap_image()
        # img_name = f"{well}_after{3}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        # a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
        # img = a1_manager.snap_image()
        # img_name = f"{well}_middle{3}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        # a1_manager.set_stage_position(StageCoord(xy=[x0+1732,y0+1000], PFSOffset=pfs_offset)) #type: ignore
        # img = a1_manager.snap_image()
        # img_name = f"{well}_before{2}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        # time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        # arm.to_liquid()
        
        # controller.inject(inject_vol_ul=3.3, mixing_cycles=1)
        
        # arm.to_home()
        
        # time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        # img = a1_manager.snap_image()
        # img_name = f"{well}_after{2}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        # a1_manager.set_stage_position(StageCoord(xy=[x0-1732,y0+1000], PFSOffset=pfs_offset)) #type: ignore
        # img = a1_manager.snap_image()
        # img_name = f"{well}_before{3}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        # time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        # arm.to_liquid()
        
        # controller.inject(inject_vol_ul=3.3, mixing_cycles=1)
        
        # arm.to_home()
        
        # time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        # img = a1_manager.snap_image()
        # img_name = f"{well}_after{3}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        
        a1_manager.set_stage_position(StageCoord(xy=[x0+2000,y0], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{4}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        arm.to_liquid()
        
        controller.inject(inject_vol_ul=5, mixing_cycles=1)
        
        arm.to_home()
        
        
        time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        arm.to_liquid()
        
        arm.to_home()
        
        time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        img = a1_manager.snap_image()
        img_name = f"{well}_after{4}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        # a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
        # img = a1_manager.snap_image()
        # img_name = f"{well}_middle{4}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        
        
        
        
        
        # a1_manager.nikon.select_focus_device('ZDrive')
        # for i in range(2):
        #     a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450])) #type: ignore
        #     a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0])) #type: ignore
        #     a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900])) #type: ignore
        #     a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0])) #type: ignore
            
            
        # a1_manager.nikon.select_focus_device('PFSOffset')
        # a1_manager.oc_settings("GFP")
        
        end = time.time()
        print(f"Total time for integrated imaging with PFS: {end - start:.2f} seconds")
        
                # Final imaging 
        for i in range(1):
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2000], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final_off{1}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0-2000,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final_off{2}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2000], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final_off{3}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0+2000,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final_off{4}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final_off_middle_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
        
        # Final imaging 
        for i in range(10):
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{1}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{2}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{3}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{4}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final_middle_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            
            
            
def integrated_imaging_384(well, x0, y0, run_dir, pfs_offset):
        # We inject in four different places equal volumes, so the sum is 10 ul - iamging before and after in the place of injection and in the middle of the well.
    
        offset = 1200
        a1_manager.nikon.select_focus_device('PFSOffset')
        a1_manager.oc_settings("GFP")
        
        for i in range(1):
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0-offset], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_previous{1}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0-offset,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_previous{2}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0+offset], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_previous{3}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0+offset,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_previous{4}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_previous_middle_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
        
        
        start = time.time()
        # Before injection
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        arm.to_liquid()
        
        controller.inject(inject_vol_ul=10, mixing_cycles=1)
        
        arm.to_home()
        
        time.sleep(1) # wait a bit for the stage to move, adjust as needed
        
        # Dip the needle in the liquid to avoid dripping
        arm.to_liquid()
        arm.to_home()
       
        
        img = a1_manager.snap_image()
        img_name = f"{well}_after{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        

        
        end = time.time()
        print(f"Total time for integrated imaging with PFS: {end - start:.2f} seconds")
        
                # Final imaging 
        for i in range(1):
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0-offset], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final_off{1}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0-offset,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final_off{2}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0+offset], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final_off{3}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0+offset,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final_off{4}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final_off_middle_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
        
        # Final imaging 
        for i in range(3):
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0-offset], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{1}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0-offset,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{2}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0+offset], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{3}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0+offset,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{4}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final_middle_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
def integrated_imaging(well, x0, y0, run_dir, pfs_offset):
        # We inject in four different places equal volumes, so the sum is 10 ul - iamging before and after in the place of injection and in the middle of the well.
       
        a1_manager.oc_settings("GFP")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_baseline{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_baseline{3}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_baseline{2}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_baseline{4}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before_middle.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
    
        
        # Before imaging
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
        
        img = a1_manager.snap_image()
        img_name = f"{well}_after{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        
        # # Middle 1
        # a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore
        # img = a1_manager.snap_image()
        # img_name = f"{well}_middle{1}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        
        
        a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{2}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
        
        img = a1_manager.snap_image()
        img_name = f"{well}_after{2}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        # a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore
        # img = a1_manager.snap_image()
        # img_name = f"{well}_middle{2}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900]))  #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{3}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
        
        img = a1_manager.snap_image()
        img_name = f"{well}_after{3}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        # a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore
        # img = a1_manager.snap_image()
        # img_name = f"{well}_middle{3}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{4}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
        
        img = a1_manager.snap_image()
        img_name = f"{well}_after{4}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        # a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore
        # img = a1_manager.snap_image()
        # img_name = f"{well}_middle{4}.tif"
        # imwrite(run_dir / img_name, img, compression='zlib')
        # print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_after_middle.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
                # After imaging 
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_final{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_final{2}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_final{3}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_final{4}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")

def integrated_imaging_middle(well, x0, y0, run_dir, pfs_offset):
        # We inject in four different places equal volumes, so the sum is 10 ul - iamging before and after in the place of injection and in the middle of the well.
    
        a1_manager.nikon.select_focus_device('PFSOffset')
        a1_manager.oc_settings("GFP")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_baseline{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0-2700,y0], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_baseline{2}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_baseline{3}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_baseline{4}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_baseline_middle.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        
        a1_manager.nikon.select_focus_device('ZDrive')
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore
        controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450], PFSOffset=pfs_offset)) #type: ignore
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore
        controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
        a1_manager.set_stage_position(StageCoord(xy=[x0-2700,y0], PFSOffset=pfs_offset)) #type: ignore
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore
        controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900], PFSOffset=pfs_offset))  #type: ignore

        a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore 
        controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
        a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0], PFSOffset=pfs_offset)) #type: ignore
       
        

        a1_manager.nikon.select_focus_device('PFSOffset')
        a1_manager.oc_settings("GFP")
        
        for i in range(33):
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{1}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0-2700,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{2}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{3}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final{4}_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_final_middle_c{i}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
  

if __name__ == "__main__":
    from a1_manager.microscope_hardware.nanopick.devices.valve import PICController
    from a1_manager.microscope_hardware.nanopick.devices.marZ import MarZ
    from pycromanager import Core
    controller = PICController(needle_size=50, pressure=0.3, port="COM8")
    a1_manager = A1Manager(objective = '20x', lamp_name = 'pE-800', focus_device  = 'PFSOffset')
    run_dir = Path('D:\\Zsuzsi\\20260618_automated_injection_384well_plate')
    arm = MarZ(core=Core(), dish='384well') # type: ignore
    # well = 'A1'
    # dish_calib = {}
    # keys = []
    pfs_offset = 8260

    # # Load the dish calibration data to get the center position of the wells for washing effect monitoring
    # dish_calib_path = Path(r"C:\Users\uManager\Documents\__repos__\GEM_suite\A1_manager\config\calib_384well.json")
    # with open(dish_calib_path, 'r') as f:
    #     dish_calib: dict[str, dict[str, Any]]= json.load(f)
    #     keys = list(dish_calib.keys())
            
    # # Move to the center of the well based on the calibration data
    # well_data = dish_calib.get(well, {})
    # x0, y0 = well_data['center']
    # a1_manager.set_stage_position(StageCoord(xy=[x0,y0], PFSOffset=pfs_offset)) #type: ignore - top
    # a1_manager.set_stage_position(StageCoord(xy=[x0-1732,y0+1000], PFSOffset=pfs_offset)) #type: ignore
    from a1_manager.dish_manager.dish_calibration.dish_384well import Dish384Well
    from a1_manager import CONFIG_DIR
    from a1_manager.microscope_hardware.nikon import NikonTi2
    nikon = NikonTi2(core = Core(), objective = '20x')
    calib_name = f"calib_384well.json"
    calib_temp_path = CONFIG_DIR.joinpath(calib_name)
    dish_calibrator = Dish384Well(calib_path=calib_temp_path)
    calibration_data = dish_calibrator._calibrate_dish(nikon)
    print(calibration_data["P24"].center[0])  # Print the calibration data for well A1
    
    
    # from a1_manager.microscope_hardware.nanopick.devices.marZ import MarZ
    # arm = MarZ(core=core, dish='384well')
    #well = 'E1'
    
    # import time
    # x0 = calibration_data[well].center[0]
    # y0 = calibration_data[well].center[1]
    
    # a1_manager.set_stage_position(StageCoord(xy=[x0, y0]))  
    
    
    
    
    
    # #get all the keys in the calibration data
    # well_keys = list(calibration_data.keys())
    # # go through all the wells and print their center coordinates
    # for well in well_keys:
    #     center = calibration_data[well].center
    #     print(f"Well {well}: Center coordinates: {center}")
    
    #     a1_manager.set_stage_position(StageCoord(xy=[calibration_data[well].center[0], calibration_data[well].center[1]]))  
    
    
    
    
    print("Current head position:", arm._get_arm_position)
    # arm.to_liquid()
    # print("Moved to liquid position:", arm._get_arm_position)
    
    # controller.inject(inject_vol_ul=2.5, mixing_cycles=1)
    
    
    # Continuous - circling during injection
    #continuous(well=well, x0=x0, y0=y0, run_dir=run_dir)
    well_list = ['A22', 'B22', 'C22', 'D22', 'E22', 'F22', 'G22', 'H22', 'I22', 'J22', 'K22', 'L22', 'M22', 'N22', 'O22', 'P22']
    for well in well_list:
        x0 = calibration_data[well].center[0]
        y0 = calibration_data[well].center[1]
        a1_manager.set_stage_position(StageCoord(xy=[x0, y0]))  
        integrated_imaging_384(well=well, x0=x0, y0=y0, run_dir= run_dir, pfs_offset=pfs_offset)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # P1: top x0,y0-2450
    # P2: bottom x0,y0+2900
    # P3: right x0-2800,y0       
    # P4: left x0+2500,y0

    #now it is a different order
    # controller.inject(inject_vol_ul=10, mixing_cycles=1)
    
    # start = time.time()
    # for i in range(1):

    #     a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450])) #type: ignore - top
    #     a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0])) #type: ignore - right
    #     a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900])) #type: ignore - bottom
    #     a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0])) #type: ignore - left
    # end = time.time()
    # print(end - start)
    # time.sleep(1) # wait a bit for the injection to finish, adjust as needed
    
    #continuous(well='G12', x0=x0, y0=y0, offset=offeset)
    # time.sleep(10)
    #divided(well='E2', x0=x0, y0=y0, offset=offeset)
    # time.sleep(10)
    #integrated_imaging_middle(well='H1', x0=x0, y0=y0, offset=offeset)
    # time.sleep(10)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    # a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0+offeset,y0])) #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0,y0+offeset])) #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0+offeset,y0]))  #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0,y0+offeset])) #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0+offeset,y0])) #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0,y0+offeset])) #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0+offeset,y0])) #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0,y0+offeset])) #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0+offeset,y0])) #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0,y0+offeset])) #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0+offeset,y0]))  #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0,y0+offeset])) #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0+offeset,y0])) #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0,y0+offeset])) #type: ignore
    # a1_manager.set_stage_position(StageCoord(xy=[x0+offeset,y0])) #type: ignore