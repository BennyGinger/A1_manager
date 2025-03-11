from dataclasses import dataclass


@dataclass
class DishCalibManager():
    """Main class to calibrate a dish. The subclasses are the different types of dishes that can be calibrated."""
    
    _dish_classes: dict[str, type['DishCalibManager']] = {}
    
    def __init_subclass__(cls, dish_name: str = None, **kwargs) -> None:
        """Automatically registers subclasses with a given dish_name. Meaning that the subclasses of DishCalibrationManager will automatically filled the _dish_classes dictionary. All the subclasses must have the dish_name attribute and are stored in the 'dish_calibration/' folder."""
        
        super().__init_subclass__(**kwargs)
        if dish_name:
            DishCalibManager._dish_classes[dish_name] = cls
    
    @classmethod
    def dish_calib_factory(cls, dish_name: str) -> 'DishCalibManager':
        """Factory method to create a calibration instance for the specified dish.
        
        Args:
            dish_name: The identifier for the dish type (e.g., '35mm', '96well', 'ibidi-8well').
        
        Returns:
            An instance of a subclass of DishCalibrationManager appropriate for the dish.
        
        Raises:
            ValueError: If the dish_name is not recognized."""
        
        dish_class = cls._dish_classes.get(dish_name)
        if not dish_class:
            raise ValueError(f"Unknown dish name: {dish_name}")

        return dish_class()
    
    def unpack_settings(self, settings: dict) -> None:
        """Update instance attributes based on the provided settings dictionary."""
        
        for key, value in settings.items():
            if hasattr(self, key):
                setattr(self, key, value)



  