from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from .marZ import DISTANCE_FOR_CALIB, MarZ

ARM_CALIBRATION_FILE = Path(__file__).with_name("arm_calibration.json")
WELL_CALIBRATION_FILE = Path(__file__).with_name("well_needle_calibration.json")
MAX_FINE_MOVE_ARM_UNITS = 3000
# Safe waiting/focusing depth; same value that was used for the calibrations
CALIBRATION_DEPTH = DISTANCE_FOR_CALIB
# Hard limit: the arm is never sent deeper than this below home (the deepest calibrated target is ~18220).
MAX_DEPTH_BELOW_HOME = {"96well": 18600}


def _load_json(path: Path) -> dict | None:
    return json.loads(path.read_text()) if path.exists() else None


def load_arm_calibration() -> dict | None:
    return _load_json(ARM_CALIBRATION_FILE)


def load_well_calibration() -> dict | None:
    return _load_json(WELL_CALIBRATION_FILE)


class CalibratedMarZ(MarZ):
    """MarZ with positioning of the needle tip relative to the cell layer, based on ZDrive/well calibrations."""

    @property
    def arm_units_per_um(self) -> float | None:
        cal = load_arm_calibration()
        return None if cal is None else cal["arm_units_per_um"]

    @property
    def well_calibration(self) -> dict | None:
        return load_well_calibration()

    @property
    def depth_below_home(self) -> float:
        """Current arm position expressed as the distance below the home position."""
        return self._ref_position - self._get_arm_position

    def to_calibration(self) -> None:
        """Move to the safe calibration depth, well above the cells."""
        self.to_depth_below_home(CALIBRATION_DEPTH[self.dish])

    def to_depth_below_home(self, depth: float) -> None:
        """Move the arm to a distance below the home position (never above home, never deeper than the hard limit)."""
        if depth < 0:
            raise ValueError("Depth below home cannot be negative.")
        if depth > MAX_DEPTH_BELOW_HOME[self.dish]:
            raise ValueError(f"Depth {depth:.0f} exceeds the safety limit of {MAX_DEPTH_BELOW_HOME[self.dish]}; not moving.")
        self._set_arm_position(self._ref_position - depth)

    def to_height_above_cells(self, tip_z_um: float, cell_z_um: float, height_um: float) -> None:
        """
        Move the tip, currently in focus at ZDrive tip_z_um, to height_um above the cells (focus at cell_z_um).
        Uses the arm calibration (arm units per um of ZDrive).
        """
        units_per_um = self.arm_units_per_um
        if units_per_um is None:
            raise RuntimeError("No arm calibration; run tests/arm_calibration.py first.")
        move = units_per_um * (cell_z_um + height_um - tip_z_um)
        if abs(move) > MAX_FINE_MOVE_ARM_UNITS:
            raise ValueError(f"Requested arm move of {move:.0f} units is too large; refocus on the tip.")
        target = self._get_arm_position + move
        if target > self._ref_position:
            raise ValueError("Target is above the home position.")
        if self._ref_position - target > MAX_DEPTH_BELOW_HOME[self.dish]:
            raise ValueError("Target is deeper than the safety limit; not moving.")
        self._set_arm_position(target)

    def to_height_from_calibration(
        self,
        cell_z_um: float,
        height_um: float,
        max_extrapolation_um: float = 100.0,
        confirm: Callable[[float, float], bool] | None = None,
    ) -> float:
        """
        Move the tip above the cells using the multi-well calibration (no tip focusing needed).
        Args:
            cell_z_um: ZDrive value with the cells in focus.
            height_um: Wanted tip height above the cells; must match the calibrated height.
            max_extrapolation_um: Allowed distance of cell_z_um outside the calibrated range.
            confirm: Called with (depth below home, arm position) before moving; return False to abort.
        Returns:
            The arm position that was set.
        """
        cal = self.well_calibration
        if cal is None:
            raise RuntimeError("No well calibration; run tests/well_needle_calibration.py first.")
        if abs(cal["tip_height_um"] - height_um) > 1e-6:
            raise ValueError(
                f"Well calibration was made for a tip height of {cal['tip_height_um']} um, not {height_um} um; recalibrate."
            )
        low, high = min(cal["cell_z"]), max(cal["cell_z"])
        if not (low - max_extrapolation_um <= cell_z_um <= high + max_extrapolation_um):
            raise ValueError(
                f"Cell ZDrive {cell_z_um:.1f} is outside the calibrated range {low:.1f}-{high:.1f}; add wells to the calibration."
            )
        depth = cal["slope"] * cell_z_um + cal["intercept"]
        if abs(depth - CALIBRATION_DEPTH[self.dish]) > MAX_FINE_MOVE_ARM_UNITS:
            raise ValueError(f"Computed depth {depth:.0f} is too far from the calibration depth; recalibrate.")
        if depth > MAX_DEPTH_BELOW_HOME[self.dish]:
            raise ValueError(f"Computed depth {depth:.0f} exceeds the safety limit; not moving.")
        position = self._ref_position - depth
        if confirm is not None and not confirm(depth, position):
            raise RuntimeError("Arm move to the calibrated height was declined.")
        # Approach from above: never pass the target on the way down
        self.to_depth_below_home(min(depth, CALIBRATION_DEPTH[self.dish]))
        self.to_depth_below_home(depth)
        return position
