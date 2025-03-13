from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from utils.utils import find_project_root
from microscope_hardware.nikon import NikonTi2


@dataclass
class DishCalibManager(ABC):
    """Main class to calibrate a dish. The subclasses are the different types of dishes that can be calibrated."""
    
    # Class variable. Dictionary mapping dish names to their corresponding classes
    _dish_classes: ClassVar[dict[str, type['DishCalibManager']]] = {}
    # Instance variables.
    dish_name: str
    run_dir: Path
    calib_path: Path = field(init=False)
    
    def __init_subclass__(cls, dish_name: str = None, **kwargs) -> None:
        """Automatically registers subclasses with a given dish_name. Meaning that the subclasses of DishCalibrationManager will automatically filled the _dish_classes dictionary. All the subclasses must have the dish_name attribute and are stored in the 'dish_calibration/' folder."""
        
        super().__init_subclass__(**kwargs)
        if dish_name:
            DishCalibManager._dish_classes[dish_name] = cls
    
    @classmethod
    def dish_calib_factory(cls, dish_name: str, run_dir: Path) -> 'DishCalibManager':
        """Factory method to create a calibration instance for the specified dish.
        
        Args:
            dish_name: The identifier for the dish type (e.g., '35mm', '96well', 'ibidi-8well').
            run_dir: Path to the directory where the calibration files will be stored.
        
        Returns:
            An instance of a subclass of DishCalibrationManager appropriate for the dish.
        
        Raises:
            ValueError: If the dish_name is not recognized."""
        
        dish_class = cls._dish_classes.get(dish_name)
        if not dish_class:
            raise ValueError(f"Unknown dish name: {dish_name}")

        return dish_class(dish_name=dish_name, run_dir=run_dir)
    
    def __post_init__(self) -> None:
        """Create the calibration directory."""
        
        # Initialize the calibration path
        self._initialize_calibration_path()
        
        # 
        

    def _initialize_calibration_path(self):
        calib_name = f"calib_{self.dish_name}.json"
        if self.dish_name == "96well":
            root_path = find_project_root(Path(__file__).resolve()) 
            self.calib_path = root_path.joinpath("config", calib_name)
        else:
            config_path = self.run_dir.joinpath("config")
            config_path.mkdir(exist_ok=True)
            self.calib_path = config_path.joinpath(calib_name)
            
    def unpack_settings(self, settings: dict) -> None:
        """Update instance attributes based on the provided settings dictionary."""
        
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    @abstractmethod
    def calibrate_dish(self, nikon: NikonTi2, **kwargs) -> dict[str, 'DishCalibManager']:
        """Abstract method to calibrate a dish. The calibration process is specific to each dish."""
        pass



  