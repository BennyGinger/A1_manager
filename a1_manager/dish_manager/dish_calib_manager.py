from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass
from abc import ABC, abstractmethod
from pathlib import Path
import logging

from a1_manager.utils.utility_classes import WellCircleCoord, WellSquareCoord
from a1_manager.utils.utils import load_json
from a1_manager.microscope_hardware.nikon import NikonTi2

# Initialize logging
logger = logging.getLogger(__name__)

@dataclass
class DishCalibManager(ABC):
    """Main class to calibrate a dish. The subclasses are the different types of dishes that can be calibrated.
    
    Attributes:
        calib_path (Path): Path to the calibration file
    """
    # Instance variables.
    calib_path: Path
    
    @classmethod
    def dish_calib_factory(cls, dish_name: str, calib_path: Path) -> DishCalibManager:
        """
        Factory method to create a calibration instance for the specified dish.
        
        Args:
            dish_name: The identifier for the dish type (e.g., '35mm', '96well', 'ibidi-8well').
            calib_path: Path to the calibration file.
        
        Returns:
            An instance of a subclass of DishCalibrationManager appropriate for the dish.
        
        Raises:
            ValueError: If the dish_name is not recognized.
            """
         # Import classes here to avoid circular imports
        if dish_name == '35mm':
            from a1_manager.dish_manager.dish_calibration.dish_35mm import Dish35mm
            return Dish35mm(calib_path)
        elif dish_name == '96well':
            from a1_manager.dish_manager.dish_calibration.dish_96well import Dish96well
            return Dish96well(calib_path)
        elif dish_name == 'ibidi-8well':
            from a1_manager.dish_manager.dish_calibration.dish_ibidi import DishIbidi
            return DishIbidi(calib_path)
        else:
            available_dishes = ['35mm', '96well', 'ibidi-8well']
            raise ValueError(f"Unknown dish name: {dish_name}. Available dishes: {', '.join(available_dishes)}")
    
    def unpack_settings(self, settings: dict) -> None:
        """
        Update instance attributes based on the provided settings dictionary.
        """
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def calibrate_dish(self, nikon: NikonTi2, well_selection: str | list[str], overwrite: bool = False) -> dict[str, WellCircleCoord | WellSquareCoord]:
        """
        Calibrate the dish by computing the coordinates for each well. If the calibration file already exists, it will be loaded instead of recalibrating. Only the wells that will be measured (i.e., in well_selection) will be returned.
        """
        if self.calib_path.exists() and not overwrite:
            logger.info(f"Calibration file already exists at {self.calib_path}.")
            dish_calibration = load_json(self.calib_path)
            # Filter the wells based on the provided well selection
            return self._filter_wells(well_selection, dish_calibration)
        
        dish_calibration = self._calibrate_dish(nikon)
        filtered_dish_calibration = self._filter_wells(well_selection, dish_calibration)
        return filtered_dish_calibration
    
    @abstractmethod
    def _calibrate_dish(self, nikon: NikonTi2) -> dict[str, WellCircleCoord | WellSquareCoord]:
        """
        Abstract method to calibrate a dish. The calibration process is specific to each dish. It returns a dictionary mapping well names (e.g., 'A1', 'B2', etc.) to WellCircle or WellSquare objects coordinates.
        """
        pass
    
    @staticmethod
    def _filter_wells(well_selection: str | list[str], dish_measurements: dict[str, WellCircleCoord | WellSquareCoord]) -> dict[str, WellCircleCoord | WellSquareCoord]:
        """
        Filter the dish measurements based on the provided well selection. If well_selection is 'all', return all the measurements.
        """
        if isinstance(well_selection, str):
            if well_selection.lower() == 'all':
                return dish_measurements
            
            if well_selection not in dish_measurements.keys():
                raise ValueError(f"Well {well_selection} not found in dish measurements.")
            well_selection = [well_selection]
        
        return {well: coord for well, coord in dish_measurements.items() if well in well_selection}
