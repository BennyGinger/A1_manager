from pathlib import Path

from utils.utility_classes import WellCircleCoord, WellSquareCoord
from microscope_hardware.nikon import NikonTi2
from dish_manager.dish_calib_manager import DishCalibManager


def calibrate_dish(dish_name: str, run_dir: Path, nikon: NikonTi2, well_selection: list[str], overwrite: bool = False) -> dict[str, WellCircleCoord | WellSquareCoord]:
    """Calibrate the dish with the specified dish name. The calibration measurements are saved in a json file in the run directory, except for the 96well dish where the calibration measurements are pre-defined."""
    
    # Initialize the dish calibration manager
    dish = DishCalibManager.dish_calib_factory(dish_name, run_dir)
    
    # Get the calibration measurements or calibrate the dish
    dish_calibration = dish.calibrate_dish(nikon, well_selection, overwrite)
    return dish_calibration