from dataclasses import dataclass

from dish_manager.dish_calibration.square_dish import DishCalib_Ibidi
from dish_manager.dish_calibration.round_dish import DishCalib_35mm, DishCalib_96well


@dataclass
class DishCalib():
    """Main class to calibrate a dish. The subclasses are the different types of dishes that can be calibrated."""
    
    _dish_classes: dict[str, 'DishCalib'] = {
            '35mm': DishCalib_35mm,
            '96well': DishCalib_96well,
            'ibidi-8well': DishCalib_Ibidi}
    
    def get_dish_calib_instance(self, dish_name: str) -> 'DishCalib':
        
        # Get the class based on dish_name
        dish_class = self._dish_classes.get(dish_name)
        if not dish_class:
            raise ValueError(f"Unknown dish name: {dish_name}")

        # Instantiate and return the appropriate subclass
        return dish_class()
    
    def unpack_settings(self, settings: dict) -> None:
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)



  