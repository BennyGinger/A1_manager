from __future__ import annotations # Enable type annotation to be stored as string

import logging

from a1_manager.microscope_hardware.nikon import NikonTi2


def prompt_for_center(nikon: 'NikonTi2') -> tuple[float, float]:
    """Prompt the user to move the stage to the center of the dish."""
    
    input("Move the center of the objective to the center of the well A1 and press 'Enter'")
    pos = nikon.get_stage_position()['xy']
    logging.info(f"User confirmed center position: {pos}")
    return nikon.get_stage_position()['xy']

def prompt_for_edge_points(nikon: 'NikonTi2') -> list[tuple[float, float]]:
    """Prompt the user to move the stage to the edge of the dish."""
    
    input("Move to the edge of the dish and press 'Enter'")
    point1 = nikon.get_stage_position()['xy']
    input("Move to another point of the edge of the dish and press 'Enter'")
    point2 = nikon.get_stage_position()['xy']
    input("Move to a final point of the edge of the dish and press 'Enter'")
    point3 = nikon.get_stage_position()['xy']
    logging.info(f"User confirmed three edge positions: 1:{point1}, 2:{point2}, 3:{point3}")
    return [point1, point2, point3]

def prompt_for_calibration_approval(measured_radius: float, expected_radius: float, 
                                   tolerance_lower: float, tolerance_upper: float) -> bool:
    """
    Prompt the user to approve or reject a calibration based on measured vs expected radius.
    
    Args:
        measured_radius: The radius measured during calibration
        expected_radius: The expected radius for the dish
        tolerance_lower: Lower bound of acceptable radius range
        tolerance_upper: Upper bound of acceptable radius range
    
    Returns:
        True if user approves the calibration, False if they want to restart
    """
    user_choice = input(f"Measured radius ({measured_radius:.2f} μm) is outside expected range {expected_radius:.2f} μm "
                       f"({tolerance_lower:.2f}-{tolerance_upper:.2f} μm).\n"
                       f"Do you want to:\n"
                       f"1. Use the measured radius anyway (y/yes)\n"
                       f"2. Restart calibration (n/no)\n"
                       f"Choice: ").strip().lower()
    
    if user_choice in ['y', 'yes', '1']:
        logging.info(f"User chose to proceed with measured radius: {measured_radius}")
        return True
    else:
        logging.info("User chose to restart calibration")
        return False
