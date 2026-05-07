import numpy as np

def generate_figure8_path(
    x0: float,
    y0: float,
    amplitude_x: float = 50.0,
    amplitude_y: float = 50.0,
    n_points: int = 100,
    n_loops: int = 2
):
    """
    Generate a figure-8 (lemniscate-like) path centered on (x0, y0).

    Parameters
    ----------
    x0, y0 : float
        Injection center coordinates (stage coordinates).
    amplitude_x : float
        Horizontal size of the pattern (in stage units, e.g. µm).
    amplitude_y : float
        Vertical size of the pattern.
    n_points : int
        Number of points per loop.
    n_loops : int
        Number of times to repeat the pattern.

    Returns
    -------
    list of (x, y) tuples
    """
    t = np.linspace(0, 2 * np.pi * n_loops, n_points * n_loops)

    x = x0 + amplitude_x * np.sin(t)
    y = y0 + amplitude_y * np.sin(2 * t)

    return list(zip(x, y))


def generate_vertical_figure8_path(
    x0,
    y0,
    amplitude_x=50,
    amplitude_y=50,
    n_points=100,
    n_loops=2
):

    t = np.linspace(0, 2*np.pi*n_loops, n_points*n_loops)

    # x = x0 + amplitude_x * np.sin(2 * t)
    # y = y0 + amplitude_y * np.sin(t)
    x = x0 + amplitude_x*np.cos(t)
    y = y0 + amplitude_y*np.sin(t)

    return list(zip(x, y))


def generate_orbital_shake(
    x0,
    y0,
    radius=1000,          # µm
    frequency=0.8,          # cycles per second
    duration=5,           # seconds
    points_per_cycle=40
):
    """
    Generate rapid orbital mixing trajectory.

    Parameters
    ----------
    x0, y0 : center coordinates
    radius : orbital radius in stage units (µm)
    frequency : orbital cycles per second
    duration : total shaking time
    points_per_cycle : trajectory smoothness
    """

    total_cycles = frequency * duration

    t = np.linspace(
        0,
        2 * np.pi * total_cycles,
        int(points_per_cycle * total_cycles)
    )

    x = x0 + radius * np.cos(t)
    y = y0 + radius * np.sin(t)

    return list(zip(x, y))



from a1_manager import A1Manager, StageCoord

from pathlib import Path
from tifffile import imwrite
import time
start = time.time()



a1_manager = A1Manager(objective = '10x', lamp_name = 'pE-800', focus_device  = 'PFSOffset')

from a1_manager.microscope_hardware.nanopick.devices.valve import PICController
controller = PICController(needle_size=50, pressure=0.3, port="COM8")

run_dir = Path('D:\\Zsuzsi\\20260507_stage_shaking_test\\E6')

a1_manager.oc_settings('GFP')
well = 'E6'
x0,y0 =   4205.4000000000015,3860.5999999999985
path = generate_figure8_path(
    x0=x0,
    y0=y0,
    amplitude_x=3000,
    amplitude_y=3000,
    n_points=24,
    n_loops=1
)

path_vert = generate_vertical_figure8_path(
    x0=x0,
    y0=y0,
    amplitude_x=2000,
    amplitude_y=2000,
    n_points=24,
    n_loops=1
)

# Example: aggressive mixing after injection
path_orb = generate_orbital_shake(
    x0=x0,
    y0=y0,
    radius=900,       # 0.8 mm
    frequency=0.3,     # 10 Hz
    duration=18
)


for i in range(1):

        a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{i}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_before{2}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
            
        
        for k in range(3):

            a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0])) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_before_left{3}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
            

        a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore
        end = time.time()
        print(end - start)
        controller.inject(inject_vol_ul=10, mixing_cycles=3)
        start_1 = time.time()
        for j in range(1):
            # for x, y in path_vert:
            #     #stage.move_to(x=x, y=y)  # adapt to your API
                
            #     a1_manager.set_stage_position(StageCoord(xy=[x, y])) #type: ignore
            for x, y in path_orb:
                #stage.move_to(x=x, y=y)  # adapt to your API
                
                a1_manager.set_stage_position(StageCoord(xy=[x, y])) #type: ignore
            
            print(f"Completed loop {j}")
              # wait a bit between loops, adjust as needed
        time.sleep(5)
        end_1 = time.time()
        print(end_1 - start_1)
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0-2450])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_after{0}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0+2900])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_after{1}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        
        a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0])) #type: ignore
        img = a1_manager.snap_image()
        img_name = f"{well}_after{2}.tif"
        imwrite(run_dir / img_name, img, compression='zlib')
        print(f"Saved image {img_name}")
        for k in range(180):
            # a1_manager.set_stage_position(StageCoord(xy=[x0-2800,y0])) #type: ignore
            # img = a1_manager.snap_image()
            # img_name = f"{well}_after_right{k}.tif"
            # imwrite(run_dir / img_name, img, compression='zlib')
            # print(f"Saved image {img_name}")
            
            a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0])) #type: ignore
            img = a1_manager.snap_image()
            img_name = f"{well}_after_left{k}.tif"
            imwrite(run_dir / img_name, img, compression='zlib')
            print(f"Saved image {img_name}")
        end_2 = time.time()
        print(end_2 - start)




