from pathlib import Path

from main import A1Manager
from utils.utils import create_date_savedir, load_config_file, save_config_file
from microscope_hardware.dmd.dmd_calibration_module import CalibrateFTurret


CAM_SETTINGS = {'objective':'20x','exposure_ms':150,'binning':2,'lamp_name':'pE-800','dmd_trigger_mode':'InternalExpose'}
PRESET_ARGS = {'optical_configuration':'GFP','intensity':5}
LIST_TURRETS = ['5-Duo','4-Quad']

def dmd_calibration(run_dir: Path, numb_points: int=9, overwrite: bool=False)-> None:
    # Initialize calibration
    aquisition = A1Manager(**CAM_SETTINGS)
    aquisition.oc_settings(**PRESET_ARGS)
    save_dir = create_date_savedir(run_dir,'Calibration')
    dmd_fTurret_list = [CalibrateFTurret(save_dir, fTurret) for fTurret in LIST_TURRETS]
    
    
    # Load dmd_profile and transfo matrix if exist or create empty dicts
    dmd_profile = load_config_file('dmd_profile')
    dmd_profile = {} if dmd_profile is None else dmd_profile
    transfo_matrix = aquisition.dmd.dmd_mask.transfo_matrix
    transfo_matrix = {} if transfo_matrix is None else transfo_matrix
    
    # Run calibration
    for dmd_fTurret in dmd_fTurret_list:
        # Set the turret
        aquisition.core.set_property('FilterTurret1','Label',dmd_fTurret.fTurret)
        
        # Get the fTurret dmd profile, if doesn't exist or overwrite
        if dmd_fTurret.fTurret not in dmd_profile or overwrite:
            dmd_profile[dmd_fTurret.fTurret] = dmd_fTurret.get_fTurret_profile(aquisition)
        
        # Create random point for each fTurret
        dmd_fTurret.create_dmd_point_list(aquisition, numb_points)
        
        # If transformation matrix already exists, test it
        if dmd_fTurret.fTurret in transfo_matrix and not overwrite:
            print(f"Loading transformation matrix and testing for {dmd_fTurret.fTurret} turret")
            # Test transformation matrix
            dmd_fTurret.test_transformation_matrix(aquisition)
            continue
        
        # Else create transformation matrix
        print(f"Creating transformation matrix for {dmd_fTurret.fTurret} turret")

        # Get turret matrix (convert it to list to be able to save it as json)
        transfo_matrix[dmd_fTurret.fTurret] = dmd_fTurret.get_transformation_matrix(aquisition).tolist()
        
        # Test transformation matrix
        dmd_fTurret.test_transformation_matrix(aquisition,transfo_matrix)
    
    
    # Update dmd profile and transformation matrix to Aquisition object
    save_config_file('dmd_profile', dmd_profile)
    save_config_file('transfo_matrix', transfo_matrix)
    aquisition.dmd.dmd_mask.reload_transfo_matrix()