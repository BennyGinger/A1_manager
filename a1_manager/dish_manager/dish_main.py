from pathlib import Path
from dataclasses import dataclass,field
from os.path import join
import json

import numpy as np
from python_tsp.heuristics import solve_tsp_simulated_annealing
from python_tsp.distances import euclidean_distance_matrix

from a1_manager.dish_manager.dish_calib_manager import DishCalibManager
from microscope_hardware.nikon import NikonTi2
from microscope_software.aquisition import Aquisition
from a1_manager.dish_manager.well_grid_manager import WellGridManager
from utils.utils import load_file

# TODO: Add the possibility to enter a manual dish calibration

##################################################################
############################ Main class ##########################
##################################################################
@dataclass
class Dish:
    dish_name: str # '35mm', 'ibidi-8well' or '96well'
    run_dir: Path # Path to the run directory
    well_selection: list[str]
    calib_path: Path = field(init=False)
    calib_obj: DishCalibManager = field(init=False)
    grid_obj: WellGridManager = field(init=False)
    dish_measurments: dict = field(init=False)
    
    def __post_init__(self)-> None:
        
        # Create the calibration path
        config_path = self.run_dir.joinpath('config')
        config_path.mkdir(exist_ok=True)
        calib_name = f"calib_{self.dish_name}.json"
        self.calib_path = config_path.joinpath(calib_name)
        
        # If the dish is 96well, then the calibration is fixed and no user input is needed
        if self.dish_name == '96well':
            self.load_template_calib()

    def load_template_calib(self):
        parent_path = Path(__file__).resolve().parent.parent
        calib_name = f"calib_{self.dish_name}.json"
        template_path = parent_path.joinpath('config',calib_name)
            
        # Load the template calibration file
        temp_measurments = self.load_dish_measurments(template_path)
            
        # Create a new dict with only the selected wells
        self.dish_measurments = self.filter_selected_wells(temp_measurments)
                    
        # Save the new calibration file
        self.save_dish_measurments()

    def config_dish(self, fTurret: str | None)-> None:
        # Get the dish calibration and grid object, the instances will be created based on the dish name
        self.calib_obj = DishCalibManager().dish_calib_factory(self.dish_name)
        
        if fTurret is not None:
            # load the DMD profile and get the grid object
            dmd_profile = load_file('dmd_profile')
            if dmd_profile is None:
                raise FileNotFoundError("No dmd_profile file found. Please calibrate the dmd first.")
            self.grid_obj = WellGridManager(dmd_profile[fTurret]['center_xy_corr_pix']).load_subclass_instance(self.dish_name)
        else:
            # If no DMD attached then use the default center correction, i.e. [0,0]
            self.grid_obj = WellGridManager([0, 0]).load_subclass_instance(self.dish_name)
                 
    def save_dish_measurments(self)-> None:
        with open(join(self.calib_path), "w") as outfile:
            json.dump(self.dish_measurments, outfile)
    
    def load_dish_measurments(self, path: Path | None = None)-> dict[str,dict]:
        if path is None:
            path = self.calib_path
            
        print(f"Loading dish calibration from {path}")
        with open(path) as json_file:
            dish_measurments: dict[str,dict] = json.load(json_file)
        return dish_measurments
        
    def filter_selected_wells(self, temp_measurments: dict[str, dict])-> dict[str, dict]:
        dish_measurments = {}
        for k, v in temp_measurments.items():
            if k in self.well_selection:
                dish_measurments[k] = v
        return dish_measurments
 
    def retrieve_dish_measurements(self)-> dict[str, dict] | dict:
        if hasattr(self, 'dish_measurments'):
            return self.dish_measurments
        
        if self.calib_path.exists():
            return self.load_dish_measurments()
        
        return dict()
    
    @staticmethod
    def get_random_well_points(points_coord: dict, fov_amount: int)-> dict:
        """Returns a random subset of points from the input dict of coordinates. The number of points is defined by the fov_amount. The function solves the TSP problem for the input points and returns the shortest path between them."""
        
        # Generate a random list of unique integers and coordinates 
        random_indices = sorted(np.random.choice(range(len(points_coord)), size=fov_amount, replace=False))
        points_lst = [points_coord[i] for i in random_indices]
        xy_lst = [point['xy'] for point in points_lst]
        
        # Calculate the distance matrix
        distance_matrix = euclidean_distance_matrix(np.array(xy_lst))
        
        # Find the shortest path between points, i.e. solve the TSP problem
        sorted_indices, _ = solve_tsp_simulated_annealing(distance_matrix)
        sorted_points = [points_lst[i] for i in sorted_indices]
        
        # Create new dict with the generated random points
        return {i: point for i, point in enumerate(sorted_points)}
    
    
    ######################### Main Methods #########################
    def get_dish_measurments(self, nikon: NikonTi2, overwrite: bool=False, **kwargs)-> None:
        # Load the dish calibration if it exists
        self.dish_measurments: dict[str, dict] | dict = self.retrieve_dish_measurements()
        
        # Check if the calibration is already done for the selected wells
        if sorted(list(self.dish_measurments.keys())) == sorted(self.well_selection) and not overwrite:
            return None
        
        # If not calibrate the dish
        temp_measurments = self.calib_obj.calibrate_dish(nikon, **kwargs)
        
        # Save only the selected wells
        self.dish_measurments = self.filter_selected_wells(temp_measurments)
        self.save_dish_measurments()

    def generate_dish_grid(self, aquisition: Aquisition, numb_field_view: int=None, overlap: float=None, n_corners_in: int=4)-> tuple[dict[int,dict]]:
        if numb_field_view is not None:
            overlap = None # Then the grid will be maximised, i.e. with the optimum overlap
        
        if overlap is not None:
            overlap = overlap / 100 # Convert from % to decimal

        # Reload the dish measurements
        self.dish_measurments = self.load_dish_measurments()
        
        dish_grid = {}
        for well in self.dish_measurments.keys():
            # load the number of corners in the well, if the well is a circle
            if self.dish_name == 'ibidi-8well':
                well_grid = self.grid_obj.create_well_grid(aquisition, self.dish_measurments[well], overlap=overlap)
            else:
                well_grid = self.grid_obj.create_well_grid(aquisition, self.dish_measurments[well], overlap=overlap, n_corners_in=n_corners_in)

            # If field view is defined, then select a random subset of points
            if numb_field_view is not None: 
                well_grid = self.get_random_well_points(well_grid, numb_field_view)
            # Add well grid to dish grid
            dish_grid[well] = well_grid
        return dish_grid
    

#############################################################################
################################## Test #####################################
#############################################################################
if __name__ == '__main__':
    
    
    from tifffile import imwrite    
    from utils.utils import progress_bar

    settings = {'aquisition_settings':{'objective':'20x', # Only 10x or 20x are calibrated for now
                                        'lamp_name':'DiaLamp',  # 'pE-800','pE-4000','DiaLamp'
                                        'focus_device':'PFSOffset'},
    
    'preset_seg': {'optical_configuration':'bf', # Channel to seg for analysis
                  'intensity': 20}, # 0-100%
                   
    'dish_settings': {'dish_name': '96well', # '35mm' 'ibidi-8well' '96well'
                     'overwrite_calib': False, # if True, will overwrite the calibration file
                     'dmd_window_only': False, # if True, will only use the dmd window size to generate points, otherwise will use the whole image size
                     'well_selection': ['H12'], # if 'all', will do all possible wells, otherwise enter a list of wells ['A1','A2',...]
                     'numb_field_view' : None, # if None, will run the whole well --> 35mm dish full coverage has 1418 field of view
                     'overlap': None}, # in 0-100% Only applicable to complete well coverage (i.e. 'numb_field_view'=None). if None then will use optimal overlap for the dish
    }
    
    # Initialise mm and set up microscope
    aquisition = Aquisition(**settings['aquisition_settings'])
    aquisition.oc_settings(**settings['preset_seg'])
   
    run_dir = Path(r'D:\Boldi\LTB4_lib\test2')
    run_dir.mkdir(exist_ok=True)
    
    init_dish = {k:v for k,v in settings['dish_settings'].items() if k in ['dish_name', 'well_selection']}
    init_dish['run_dir'] = run_dir
    grid_dish = {k:v for k,v in settings['dish_settings'].items() if k in ['dmd_window_only', 'numb_field_view', 'overlap']}
    grid_dish['aquisition'] = aquisition
    
    fturret = None
    
    dish = Dish(**init_dish)
    dish.config_dish(fturret)
    
    # Calibrate dish #top_left_center=[49205.4, -32139.4]
    dish.get_dish_measurments(aquisition.nikon,overwrite=False)
    
    dish_grid = dish.generate_dish_grid(**grid_dish)
    
    with open(run_dir.joinpath('config','dish_grid.json'), "w") as outfile:
        json.dump(dish_grid, outfile)
    
    
    img_path = run_dir.joinpath('images')
    img_path.mkdir(exist_ok=True)
    for well, well_point in dish_grid.items():
        for instance, point in progress_bar(well_point.items()):
            aquisition.nikon.set_stage_position(point)
            # img = aquisition.snap_image()
            # imwrite(img_path.joinpath(f"{well}_{instance}.tif"),img)
    
    # for well, well_point in dish_grid.items():
    #     for instance, point in progress_bar(well_point.items()):
    #         aquisition.nikon.set_stage_position(point)