from dataclasses import dataclass, field

from dish_manager.dish_utils.geometry_utils import compute_optimal_overlap


@dataclass
class GridBuilder:
    
    window_size: tuple[float, float] = field(init=False)
    axis_length: tuple[float, float] = field(init=False)
    overlaps: tuple[float,float] = field(init=False)
    num_rects: tuple[int,int] = field(init=False)
    align_correction: tuple[float,float] = field(init=False)
    
    def _define_overlap(self, overlap: float | None)-> None:
        """Sets the overlap between rectangles. If an overlap is provided, it is used; otherwise, computes an optimal value."""
        
        if overlap is not None:
            self.overlaps = (overlap, overlap)
        else:
            self.overlaps = compute_optimal_overlap(self.window_size, *self.axis_length)
    
    def _define_number_of_rectangles(self) -> None:
        """
        Determines the maximum number of rectangles that can fit along each axis.
        """
        x_axis, y_axis = self.axis_length
        num_x = int(x_axis) // int(self.window_size[0] * (1 - self.overlaps[0]))
        num_y = int(y_axis) // int(self.window_size[1] * (1 - self.overlaps[1]))
        self.num_rects = (num_x, num_y)
        
    def _align_rectangles_on_axis(self) -> None:
        """
        Computes the correction factors to center the grid along the x and y axes.
        """
        x_axis, y_axis = self.axis_length
        corr_x = (x_axis - (self.window_size[0] * self.num_rects[0] * (1 - self.overlaps[0]))) / 2
        corr_y = (y_axis - (self.window_size[1] * self.num_rects[1] * (1 - self.overlaps[1]))) / 2
        self.align_correction = (corr_x, corr_y)
    
    def calculate_layout_parameters(self, window_size: tuple[float, float], axis_length: tuple[float, float], overlap: float | None) -> tuple[tuple[int,int], tuple[float,float]]:
        """Calculate the layout parameters for the grid. The layout parameters include the number of rectangles that can fit along each axis and the correction factors to center the grid along the x and y axes."""
        
        # Set the class attributes
        self.window_size = window_size
        self.axis_length = axis_length
        
        # Define the overlap between rectangles
        self._define_overlap(overlap)
        
        # Define the number of rectangles that can fit along each axis
        self._define_number_of_rectangles()
        
        # Align the rectangles along the x and y axes
        self._align_rectangles_on_axis()
        
        return self.num_rects, self.align_correction
        
    
    