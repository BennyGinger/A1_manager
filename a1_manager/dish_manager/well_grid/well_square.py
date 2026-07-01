from __future__ import annotations # Enable type annotation to be stored as string
from dataclasses import dataclass, field
import math
import logging

import numpy as np

from a1_manager.utils.utility_classes import StageCoord, WellSquareCoord, WellBaseCoord
from a1_manager.dish_manager.well_grid_manager import WellGridManager


@dataclass
class WellSquareGrid(WellGridManager):
    x_tl: float = field(init=False)
    y_tl: float = field(init=False)
    x_br: float = field(init=False)
    y_br: float = field(init=False)
    well_length: float = field(init=False)
    well_width: float = field(init=False)
    
    @property
    def axis_length(self) -> tuple[float, float]:
        """Return the length (x) and width (y) of the square well."""
        if not hasattr(self, 'well_length') or not hasattr(self, 'well_width'):
            raise ValueError("well dimensions not set. Call unpack_well_properties() first.")
        return (self.well_length, self.well_width)

    def unpack_well_properties(self, well_measurements: WellSquareCoord, n_corners_in: int)-> None:  # type: ignore[override]
        """
        Unpack the well properties from the well measurements.
        Maps index 0 to X and index 1 to Y to align with calibration.
        """
        topleft = well_measurements.top_left
        bottomright = well_measurements.bottom_right
        
        self.x_tl, self.y_tl = topleft if topleft is not None else (0, 0)
        self.x_br, self.y_br = bottomright if bottomright is not None else (0, 0)
        
        # Keep original physical vectors intact (X decreases, Y increases)
        self.well_length = self.x_br - self.x_tl  
        self.well_width = self.y_br - self.y_tl   
    
    def generate_coordinates_per_axis(self, num_rects: tuple[int, int], align_correction: tuple[float, float]) -> tuple[list, list]:
        """
        Calculates coordinates by stepping precisely by the camera window size.
        Forces align_correction to (0,0) and calculates gapless edge-to-edge coverage.
        """
        # 1. Read camera sensor footprints directly from your class
        fov_h = self.window_size[0] if isinstance(self.window_size, (tuple, list)) else self.window_size
        fov_w = self.window_size[1] if isinstance(self.window_size, (tuple, list)) else self.window_size
        
        # 2. Determine physical directional signs (+1 or -1) from top-left to bottom-right
        dir_x = 1.0 if (self.x_br >= self.x_tl) else -1.0
        dir_y = 1.0 if (self.y_br >= self.y_tl) else -1.0
        
        # 3. Get total absolute dimensions of the well cavity
        abs_well_len = abs(self.well_length)
        abs_well_wid = abs(self.well_width)
        
        # 4. OVERRIDE: Calculate the real number of frames needed to span the well with ZERO gaps.
        needed_cols = math.ceil(abs_well_len / fov_w)
        needed_rows = math.ceil(abs_well_wid / fov_h)
        
        # 5. Define step lengths to equal the camera dimension exactly (Edge-to-Edge Tiling)
        step_x = dir_x * fov_w
        step_y = dir_y * fov_h
        
        # 6. Calculate total covered footprint area to center the grid perfectly over the well
        total_covered_x = step_x * needed_cols
        total_covered_y = step_y * needed_rows
        
        # Force align_correction to (0,0) behavior internally by ignoring the argument input
        x_start = self.x_tl + (step_x / 2) - ((total_covered_x - self.well_length) / 2)
        y_start = self.y_tl + (step_y / 2) - ((total_covered_y - self.well_width) / 2)
        
        # 7. Generate lists of coordinates by multiplying clean step increments
        x_coords = [x_start + (step_x * c) for c in range(needed_cols)]
        y_coords = [y_start + (step_y * r) for r in range(needed_rows)]
        
        logging.info(f"[GRID CONTROL] Overrode layout restriction. Generated a gapless {needed_rows}x{needed_cols} grid.")
        
        # Returns (Y list, X list) strictly matching parent method signature expectations
        return x_coords, y_coords

    def update_well_grid(self, well_grid: dict[int, StageCoord], temp_point: StageCoord, count: int, x: float, y: float) -> int:
        """Update the well grid with the new rectangle center coordinates."""
        offset_x, offset_y = self.window_center_offset_um
        adjusted_x = x + offset_x
        adjusted_y = y + offset_y
        
        point = temp_point.copy()
        point.xy = (adjusted_x, adjusted_y)
        well_grid[count] = point
        return count + 1


if __name__ == "__main__":
    import math

    # 1. Initialize your class instance with your current settings
    grid_manager = WellSquareGrid()
    
    # 2. Setup your mock well measurements using the outputs of your calibration
    # Replace these coordinates with your actual calibration test points if desired
    test_well = WellSquareCoord(
        top_left=(-19113.465217391305,-35620.1),
        bottom_right=( -21913.465217391305,-32820.1)   
    )
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import numpy as np

    grid_manager.window_size = (667.0, 667.0)  # [height, width] in microns
    num_fields = (4, 4)                       # (rows, columns)
    tweaks = (0.0, 0.0)                       # (y_correction, x_correction)
    
    # Unpack measurements
    grid_manager.unpack_well_properties(test_well,4)
    
    # 3. EXECUTE YOUR EXACT FUNCTION TO GET THE RAW OUTPUT ARRAYS
    x_coords, y_coords = grid_manager.generate_coordinates_per_axis(num_fields, tweaks)
    for y_val in y_coords:
                for x_val in x_coords:

                    
                    # PRINT EACH CALCULATED RECTANGLE CENTER RIGHT HERE
                    print(f" {x_val:^16.2f} | {y_val:^16.2f}")
                    
    
    # =================================================================
    # GRAPHICAL VISUALIZATION BLOCK (READING DIRECTLY FROM OUTPUT)
    # =================================================================
    # Read camera size properties directly from the manager object arrays
    fov_h = grid_manager.window_size[0]
    fov_w = grid_manager.window_size[1]
    
    fig, ax = plt.subplots(figsize=(9, 9))

    # Draw the physical Outer Well Boundary using calibration data
    well_w = grid_manager.x_br - grid_manager.x_tl
    well_h = grid_manager.y_br - grid_manager.y_tl
    
    well_rect = patches.Rectangle(
        (grid_manager.x_tl, grid_manager.y_tl), well_w, well_h, 
        linewidth=3, edgecolor='black', facecolor='none', linestyle='-', label='Physical Well Border'
    )
    ax.add_patch(well_rect)

    # Draw every single FOV rectangle box strictly using the output array values
    # Sets translucent fills to reveal any gaps or overlapping patterns automatically
    for y in y_coords:
        for x in x_coords:
            # Calculate the box corners relative to the raw center coordinates
            box_left = x - (fov_w / 2)
            box_bottom = y - (fov_h / 2)
            
            # Create translucent camera frame footprint box
            fov_box = patches.Rectangle(
                (box_left, box_bottom), fov_w, fov_h,
                linewidth=1.2, edgecolor='darkred', facecolor='red', alpha=0.18
            )
            ax.add_patch(fov_box)
            
            # Draw a point on the exact center returned by your loop arrays
            ax.plot(x, y, color='crimson', marker='o', markersize=4)

    # Automatically fit plot frame to encompass the well boundaries + small padding margins
    pad_x = abs(well_w) * 0.1
    pad_y = abs(well_h) * 0.1
    
    ax.set_xlim(min(grid_manager.x_tl, grid_manager.x_br) - pad_x, max(grid_manager.x_tl, grid_manager.x_br) + pad_x)
    ax.set_ylim(min(grid_manager.y_tl, grid_manager.y_br) - pad_y, max(grid_manager.y_tl, grid_manager.y_br) + pad_y)

    # Labels and Grid customization
    ax.set_xlabel('Microscope Stage X Coordinate (μm)', fontsize=10)
    ax.set_ylabel('Microscope Stage Y Coordinate (μm)', fontsize=10)
    ax.set_title(f'Live Visual Grid Analysis: {len(y_coords)}x{len(x_coords)} FOVs Inside Well Layout', fontsize=12, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.6, color='gray')
    ax.legend(loc='upper right')
    
    # Force 1:1 pixel scaling so squares don't appear distorted as rectangles
    plt.gca().set_aspect('equal', adjustable='box')
    
    print("[VISUALIZATION COMPLETE] Displaying generated grid interface map plot...")
    plt.show()
