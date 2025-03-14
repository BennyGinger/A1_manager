from __future__ import annotations # Enable type annotation to be stored as string
import math

import numpy as np
from python_tsp.heuristics import solve_tsp_simulated_annealing
from python_tsp.distances import euclidean_distance_matrix

from a1_manager.utils.utility_classes import StageCoord


def find_circle(point1: tuple[float, float], point2: tuple[float, float], point3: tuple[float, float]) -> tuple[tuple[float, float], float]:
    """Compute the center and radius of a circle passing through three points.
    
    Args:
        point1: A tuple (x1, y1) representing the first point.
        point2: A tuple (x2, y2) representing the second point.
        point3: A tuple (x3, y3) representing the third point.
    
    Returns:
        A tuple containing:
            - (center_x, center_y): The center of the circle.
            - radius: The circle's radius.
    
    Raises:
        ValueError: If the three points are collinear."""
    
    (x1, y1), (x2, y2), (x3, y3) = point1, point2, point3

    # Calculate the denominator, which is 2 times the determinant of the matrix
    denominator = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if denominator == 0:
        raise ValueError("The given points are collinear; a unique circle cannot be determined.")

    # Calculate the circle's center using the circumcenter formula
    center_x = ((x1**2 + y1**2) * (y2 - y3) +
                (x2**2 + y2**2) * (y3 - y1) +
                (x3**2 + y3**2) * (y1 - y2)) / denominator

    center_y = ((x1**2 + y1**2) * (x3 - x2) +
                (x2**2 + y2**2) * (x1 - x3) +
                (x3**2 + y3**2) * (x2 - x1)) / denominator

    # Compute the radius using the distance from the center to one of the points
    radius = math.sqrt((center_x - x1)**2 + (center_y - y1)**2)
    
    return (center_x, center_y), radius

def compute_optimal_overlap(window_size: tuple[float, float], well_width: float, well_length: float) -> tuple[float, float]:
    """
    Computes the optimal overlap based on the rectangle size and a given width and length of the dish.
    """
    # If overlap is None, then determine optimum overlap
    rectS_in_y = (2 * well_width) / window_size[1]
    rectS_in_x = (2 * well_length) / window_size[0]
    
    ceiled_rectS_in_y = np.ceil(rectS_in_y)
    ceiled_rectS_in_x = np.ceil(rectS_in_x)
    overlap_y = (ceiled_rectS_in_y - rectS_in_y) / ceiled_rectS_in_y
    overlap_x = (ceiled_rectS_in_x - rectS_in_x) / ceiled_rectS_in_x
    return (overlap_x, overlap_y)


def randomise_fov(well_grid: dict[int, StageCoord], numb_field_view: int) -> dict [int, StageCoord]:
    """Returns a random subset of points from the input dict of coordinates. The number of points is defined by the fov_amount. The function solves the TSP problem for the input points and returns the shortest path between them."""
    
    # Generate a random list of unique integers and coordinates 
    random_indices = sorted(np.random.choice(range(len(well_grid)), size=numb_field_view, replace=False))
    points_lst = [well_grid[i] for i in random_indices]
    xy_lst = [point['xy'] for point in points_lst]
    
    # Calculate the distance matrix
    distance_matrix = euclidean_distance_matrix(np.array(xy_lst))
    
    # Find the shortest path between points, i.e. solve the TSP problem
    sorted_indices, _ = solve_tsp_simulated_annealing(distance_matrix)
    sorted_points = [points_lst[i] for i in sorted_indices]
    
    # Create new well grid with the generated random points optimised for the shortest path
    return {i: point for i, point in enumerate(sorted_points)}