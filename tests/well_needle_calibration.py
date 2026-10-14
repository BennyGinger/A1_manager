from __future__ import annotations

import json

import numpy as np

from a1_manager import A1Manager
from brightfield import brightfield
from a1_manager.microscope_hardware.nanopick.devices.needle_height import CalibratedMarZ, WELL_CALIBRATION_FILE

DISH = "96well"
OBJECTIVE = "10x"
EXPOSURE_MS = 50
TIP_HEIGHT_ABOVE_CELLS_UM = 100
MIN_WELLS = 3


def calibrate_wells() -> None:
    """Run with an empty or buffer-filled needle. Measures the needle depth for several wells and fits it against the cell ZDrive."""
    a1_manager = A1Manager(
        objective=OBJECTIVE,
        exposure_ms=EXPOSURE_MS,
        lamp_name="pE-800",
        focus_device="PFSOffset",
    )
    arm = CalibratedMarZ(core=a1_manager.core, dish=DISH)
    if arm.arm_units_per_um is None:
        raise RuntimeError("Run tests/arm_calibration.py first.")

    cell_z_values: list[float] = []
    depths: list[float] = []
    try:
        with brightfield(a1_manager, EXPOSURE_MS):
            while True:
                if len(depths) >= MIN_WELLS:
                    if input(f"{len(depths)} wells measured. Add another well? [y/N] ").strip().lower() != "y":
                        break
                input(f"Well {len(depths) + 1}: move the stage to the well, focus on the cells (PFS on) and press Enter.")
                a1_manager.nikon.select_focus_device("PFSOffset")
                cell_coord = a1_manager.nikon.get_stage_position()
                cell_z = cell_coord.ZDrive

                arm.to_calibration()
                a1_manager.nikon.select_focus_device("ZDrive")
                input("PFS is off. Focus on the needle tip with the ZDrive and press Enter.")
                tip_z = a1_manager.core.get_position("ZDrive")
                print(f"Cell ZDrive={cell_z:.1f}, tip ZDrive={tip_z:.1f}, distance={tip_z - cell_z:.1f} um", flush=True)

                a1_manager.core.set_position("ZDrive", cell_z)
                a1_manager.core.wait_for_device("ZDrive")
                a1_manager.nikon.select_focus_device("PFSOffset")
                a1_manager.set_stage_position(cell_coord)

                arm.to_height_above_cells(tip_z, cell_z, TIP_HEIGHT_ABOVE_CELLS_UM)
                depth = arm.depth_below_home
                print(f"Depth below home for {TIP_HEIGHT_ABOVE_CELLS_UM} um above the cells: {depth:.0f}", flush=True)
                cell_z_values.append(cell_z)
                depths.append(depth)
                arm.to_home()
    finally:
        arm.to_home()

    slope, intercept = np.polyfit(cell_z_values, depths, 1)
    residuals = np.array(depths) - (slope * np.array(cell_z_values) + intercept)
    print(f"depth = {slope:.4f} * cell_z + {intercept:.1f}", flush=True)
    print(f"Residuals (arm units): {np.round(residuals, 1).tolist()}", flush=True)
    print(
        f"Residuals in um: {np.round(residuals / arm.arm_units_per_um, 1).tolist()}",
        flush=True,
    )

    WELL_CALIBRATION_FILE.write_text(
        json.dumps(
            {
                "tip_height_um": TIP_HEIGHT_ABOVE_CELLS_UM,
                "slope": float(slope),
                "intercept": float(intercept),
                "cell_z": cell_z_values,
                "depth_below_home": depths,
            },
            indent=2,
        )
    )
    print(f"Saved to {WELL_CALIBRATION_FILE}", flush=True)


if __name__ == "__main__":
    calibrate_wells()
