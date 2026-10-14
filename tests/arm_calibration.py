from __future__ import annotations

import json

import numpy as np
from pycromanager import Core

from a1_manager.microscope_hardware.nanopick.devices.needle_height import ARM_CALIBRATION_FILE

POSITION_COUNT = 5


def calibrate_arm() -> float:
    core = Core()
    # PFS would move the ZDrive on its own while focusing
    core.set_property("PFS", "FocusMaintenance", "Off")

    arm_positions: list[float] = []
    z_positions: list[float] = []
    print(
        "For each position: move the arm (ZAxis) by a different amount, then focus on the needle tip "
        "with the ZDrive. Always approach each position from the same direction. Press Enter to record.",
        flush=True,
    )
    for number in range(POSITION_COUNT):
        input(f"Position {number + 1}/{POSITION_COUNT}: tip in focus? Press Enter.")
        arm = core.get_position("ZAxis")
        z = core.get_position("ZDrive")
        arm_positions.append(arm)
        z_positions.append(z)
        print(f"  ZAxis={arm:.1f}  ZDrive={z:.1f}", flush=True)

    slope, intercept = np.polyfit(z_positions, arm_positions, 1)
    residuals = np.array(arm_positions) - (slope * np.array(z_positions) + intercept)
    print(f"Arm units per um of ZDrive: {slope:.4f}", flush=True)
    print(f"Residuals (arm units): {np.round(residuals, 1).tolist()}", flush=True)

    ARM_CALIBRATION_FILE.write_text(
        json.dumps(
            {
                "arm_units_per_um": float(slope),
                "intercept": float(intercept),
                "arm_positions": arm_positions,
                "zdrive_positions": z_positions,
            },
            indent=2,
        )
    )
    print(f"Saved to {ARM_CALIBRATION_FILE}", flush=True)
    return float(slope)


if __name__ == "__main__":
    calibrate_arm()
