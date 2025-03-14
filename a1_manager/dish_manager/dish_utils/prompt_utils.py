from __future__ import annotations # Enable type annotation to be stored as string

from microscope_hardware.nikon import NikonTi2


def prompt_for_center(nikon: 'NikonTi2') -> tuple[float, float]:
    """Prompt the user to move the stage to the center of the dish."""
    
    input("Move the center of the objective to the center of the well A1 and press 'Enter'")
    return nikon.get_stage_position()['xy']

def prompt_for_edge_points(nikon: 'NikonTi2') -> list[tuple[float, float]]:
    """Prompt the user to move the stage to the edge of the dish."""
    
    input("Move to the edge of the dish and press 'Enter'")
    point1 = nikon.get_stage_position()['xy']
    input("Move to another point of the edge of the dish and press 'Enter'")
    point2 = nikon.get_stage_position()['xy']
    input("Move to a final point of the edge of the dish and press 'Enter'")
    point3 = nikon.get_stage_position()['xy']
    return [point1, point2, point3]