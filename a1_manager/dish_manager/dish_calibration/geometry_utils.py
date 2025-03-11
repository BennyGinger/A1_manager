import math


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
