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

    x = x0 + amplitude_x * np.sin(2 * t)
    y = y0 + amplitude_y * np.sin(t)

    return list(zip(x, y))


from a1_manager import A1Manager, StageCoord

from pathlib import Path
from tifffile import imwrite
import time

a1_manager = A1Manager(objective = '10x', lamp_name = 'pE-800', focus_device  = 'PFSOffset')

from a1_manager.microscope_hardware.nanopick.devices.valve import PICController
controller = PICController(needle_size=50, pressure=0.3, port="COM8")


run_dir = Path('D:\\Zsuzsi\\20260507_stage_shaking_test\\F5')

#a1_manager.oc_settings('GFP')


well = 'F5'
x0,y0 =  13205.400000000001,12860.599999999999
a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0])) #type: ignore
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
    amplitude_x=3000,
    amplitude_y=3000,
    n_points=24,
    n_loops=1
)
time.sleep(5)
print("Starting injection and shaking...")

for i in range(1):


        
#type: ignore
        
        a1_manager.set_stage_position(StageCoord(xy=[x0,y0])) #type: ignore
        controller.inject(inject_vol_ul=10, mixing_cycles=3)
        
        for j in range(3):
            for x, y in path:
                #stage.move_to(x=x, y=y)  # adapt to your API
                
                a1_manager.set_stage_position(StageCoord(xy=[x, y])) #type: ignore
            time.sleep(2)  # wait a bit between loops, adjust as needed
            for x, y in path_vert:
                #stage.move_to(x=x, y=y)  # adapt to your API
                
                a1_manager.set_stage_position(StageCoord(xy=[x, y])) #type: ignore
            
            print(f"Completed loop {j}")
            time.sleep(2) 
              # wait a bit between loops, adjust as needed
        a1_manager.set_stage_position(StageCoord(xy=[x0+2500,y0])) #type: ignore

        time.sleep(10)
        




