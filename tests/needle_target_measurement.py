from __future__ import annotations

import json
from pathlib import Path

from a1_manager import A1Manager
from a1_manager.microscope_hardware.nanopick.devices.needle_height import CalibratedMarZ

DISH = "96well"
OBJECTIVE = "10x"
OPTICAL_CONFIGURATION = "RFP"
FILTER_WHEEL = 4
EXPOSURE_MS = 200
TIP_HEIGHT_ABOVE_CELLS_UM = 100
WELL = "A1"

NEEDLE_TARGETS_FILE = Path(__file__).with_name("needle_targets.json")


def measure_needle_target() -> float:
    """Run with an empty or buffer-filled needle, before it is loaded with ligand."""
    a1_manager = A1Manager(
        objective=OBJECTIVE,
        exposure_ms=EXPOSURE_MS,
        lamp_name="pE-800",
        focus_device="PFSOffset",
    )
    arm = CalibratedMarZ(core=a1_manager.core, dish=DISH)
    try:
        a1_manager.oc_settings(OPTICAL_CONFIGURATION, exposure_ms=EXPOSURE_MS)
        a1_manager.core.set_property("FilterWheel1", "State", FILTER_WHEEL)
        a1_manager.set_stage_position(a1_manager.nikon.get_stage_position())

        input(f"Well {WELL}: focus on the cells (PFS on) and press Enter.")
        cell_coord = a1_manager.nikon.get_stage_position()

        arm.to_calibration()
        a1_manager.nikon.select_focus_device("ZDrive")
        input("PFS is off. Focus on the needle tip with the ZDrive and press Enter.")
        tip_z = a1_manager.core.get_position("ZDrive")
        cell_z = cell_coord.ZDrive
        print(f"Tip ZDrive={tip_z:.1f}, cell ZDrive={cell_z:.1f}, distance={tip_z - cell_z:.1f} um", flush=True)

        a1_manager.core.set_position("ZDrive", cell_z)
        a1_manager.core.wait_for_device("ZDrive")
        a1_manager.nikon.select_focus_device("PFSOffset")
        a1_manager.set_stage_position(cell_coord)

        arm.to_height_above_cells(tip_z, cell_z, TIP_HEIGHT_ABOVE_CELLS_UM)
        depth = arm.depth_below_home
        print(f"Target depth below home: {depth:.0f} arm units", flush=True)

        targets = json.loads(NEEDLE_TARGETS_FILE.read_text()) if NEEDLE_TARGETS_FILE.exists() else {}
        targets[WELL] = {"depth_below_home": depth, "tip_height_um": TIP_HEIGHT_ABOVE_CELLS_UM}
        NEEDLE_TARGETS_FILE.write_text(json.dumps(targets, indent=2))
        print(f"Saved to {NEEDLE_TARGETS_FILE}", flush=True)
        return depth
    finally:
        arm.to_home()


if __name__ == "__main__":
    measure_needle_target()
