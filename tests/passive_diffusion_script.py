from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from threading import Event, Thread
from time import monotonic, sleep

from tifffile import imwrite

from a1_manager import A1Manager
from brightfield import brightfield
from a1_manager.microscope_hardware.nanopick.devices.needle_height import CalibratedMarZ
from a1_manager.microscope_hardware.nanopick.devices.valve import PICController, VALVE_2_TIME


DISH = "96well"
OBJECTIVE = "10x"
OPTICAL_CONFIGURATION = "RFP"
FILTER_WHEEL = 4
# Brightfield (dia lamp) is used to focus the cells (and the needle tip in the calibrations)
FOCUS_EXPOSURE_MS = 50
EXPOSURE_MS = 200
VALVE_PORT = "COM8"
NEEDLE_SIZE_UM = 50
PRESSURE_BAR = 0.30
INJECTION_VOLUME_UL = 10
MIXING_CYCLES = 100
MIXING_CYCLE_INTERVAL_SECONDS = 2.0
BASELINE_DURATION_SECONDS = 20
TOTAL_MEASUREMENT_SECONDS = 5 * 60
FRAME_INTERVAL_SECONDS = 1 / 3
TIP_HEIGHT_ABOVE_CELLS_UM = 100
DIFFUSION_DISTANCE = 20543# Arm units below home, not PFS units
FILENAME_LABEL = "LTB4_passive_48um_above"
WELL = "B11"
# False: compute the arm position from the arm calibration and the cell ZDrive (no per-well measurement)
USE_STORED_WELL_TARGET = False
NEEDLE_TARGETS_FILE = Path(__file__).with_name("needle_targets.json")


def to_diffusion_distance(arm: CalibratedMarZ) -> None:
    """Move to the configured diffusion distance below the arm reference position."""
    arm._set_arm_position(arm._ref_position - DIFFUSION_DISTANCE)


# False: no valve injection; the needle stays down until the measurement deadline.
INJECT = False

OUTPUT_ROOT = Path(r"D:\Zsuzsi\Diffusion experiments\2026_10_22_LTB4_c1913B_diffusion_96well")


def run_time_lapse() -> Path:
    run_dir = OUTPUT_ROOT / f"{datetime.now():%Y%m%d_%H%M%S}_{FILENAME_LABEL}"
    run_dir.mkdir(parents=True, exist_ok=False)
    
    print(f"Run folder: {run_dir}", flush=True)
    print("Connecting to microscope and valve...", flush=True)

    a1_manager = A1Manager(
        objective=OBJECTIVE,
        exposure_ms=EXPOSURE_MS,
        lamp_name="pE-800",
        focus_device="PFSOffset",
    )
    controller = (
        PICController(
            needle_size=NEEDLE_SIZE_UM,
            pressure=PRESSURE_BAR,
            port=VALVE_PORT,
        )
        if INJECT
        else None
    )
    arm: CalibratedMarZ | None = None
    arm_is_home = False

    try:
        print("Preparing arm and imaging...", flush=True)
        arm = CalibratedMarZ(core=a1_manager.core, dish=DISH)
        a1_manager.set_stage_position(a1_manager.nikon.get_stage_position())

        with brightfield(a1_manager, FOCUS_EXPOSURE_MS):
            print(
                "Focus on the cells in brightfield (same as in the needle calibration); press Enter.",
                flush=True,
            )
            input()
            cell_z = a1_manager.nikon.get_stage_position().ZDrive
        if cell_z is None:
            raise RuntimeError("Could not read the cell ZDrive position.")

        a1_manager.oc_settings(OPTICAL_CONFIGURATION, exposure_ms=EXPOSURE_MS)
        a1_manager.core.set_property("FilterWheel1", "State", FILTER_WHEEL)
        print(
            "Check RFP focus in Micro-Manager and adjust if needed; press Enter to capture baseline.",
            flush=True,
        )
        input()

        if a1_manager.core.is_sequence_running():
            a1_manager.core.stop_sequence_acquisition()
            print("Stopped live view before snapping.", flush=True)

        measurement_started = monotonic()
        measurement_deadline = measurement_started + TOTAL_MEASUREMENT_SECONDS
        baseline_deadline = measurement_started + BASELINE_DURATION_SECONDS
        print(
            f"Capturing baseline for {BASELINE_DURATION_SECONDS}s "
            f"(target {1 / FRAME_INTERVAL_SECONDS:.1f} frames/s)...",
            flush=True,
        )
        frame_number = 0
        next_frame_time = measurement_started
        while monotonic() < baseline_deadline:
            image = a1_manager.snap_image(dmd_exposure_sec=EXPOSURE_MS / 1000)
            imwrite(run_dir / f"baseline_{FILENAME_LABEL}_{frame_number:06d}.tif", image)
            frame_number += 1
            next_frame_time = max(next_frame_time + FRAME_INTERVAL_SECONDS, monotonic())
            frame_delay = next_frame_time - monotonic()
            if frame_delay > 0:
                sleep(frame_delay)

        if controller is not None:
            print(f"Moving arm to calibration position; starting {MIXING_CYCLES} injection cycles...", flush=True)
        else:
            print("Moving arm to the target position; needle stays down until the five-minute measurement ends...", flush=True)
        to_diffusion_distance(arm)
        valve_time = 0
        if controller is not None:
            valve_time = (
                round(INJECTION_VOLUME_UL)
                if controller.test_mode
                else round(
                    controller._convert_volume_to_time(INJECTION_VOLUME_UL)
                    / MIXING_CYCLES
                )
            )
        injection_started = monotonic()
        injection_done = Event()
        injection_errors: list[Exception] = []

        def run_injection_cycles() -> None:
            try:
                for cycle_number in range(MIXING_CYCLES):
                    cycle_started = monotonic()
                    controller._set_delay(valve_time)
                    controller._set_valve_time(1, valve_time)
                    controller._open_valves_sequence("K")
                    sleep((valve_time + VALVE_2_TIME) / 1000)

                    remaining_interval = MIXING_CYCLE_INTERVAL_SECONDS - (monotonic() - cycle_started)
                    if remaining_interval > 0:
                        sleep(remaining_interval)

                    completed_cycles = cycle_number + 1
                    if completed_cycles % 10 == 0 or completed_cycles == MIXING_CYCLES:
                        elapsed = monotonic() - injection_started
                        remaining_cycles = MIXING_CYCLES - completed_cycles
                        estimated_remaining = elapsed / completed_cycles * remaining_cycles
                        print(
                            f"Injection: {completed_cycles}/{MIXING_CYCLES} cycles; "
                            f"{elapsed:.0f}s elapsed, about {estimated_remaining:.0f}s remaining",
                            flush=True,
                        )
            except Exception as error:
                injection_errors.append(error)
            finally:
                injection_done.set()

        def hold_needle_down() -> None:
            remaining_measurement = max(0, measurement_deadline - monotonic())
            sleep(remaining_measurement)
            injection_done.set()

        injection_thread = Thread(
            target=run_injection_cycles if controller is not None else hold_needle_down,
            name="valve-injection" if controller is not None else "needle-hold",
        )
        injection_thread.start()
        print(
            f"Continuing acquisition until {TOTAL_MEASUREMENT_SECONDS}s from baseline start "
            f"at a target of {1 / FRAME_INTERVAL_SECONDS:.1f} frames/s...",
            flush=True,
        )
        arm_lift_started = False

        next_status_update = injection_started + 30
        frame_number = 0
        next_frame_time = injection_started
        try:
            while monotonic() < measurement_deadline:
                if injection_errors:
                    break

                now = monotonic()
                if injection_done.is_set():
                    if not arm_lift_started:
                        print("Needle hold/injection complete; lifting needle while imaging continues...", flush=True)
                        arm.start_to_home()
                        arm_lift_started = True

                image = a1_manager.snap_image(dmd_exposure_sec=EXPOSURE_MS / 1000)
                imwrite(
                    run_dir / f"passive_diffusion_{FILENAME_LABEL}_{frame_number:06d}.tif",
                    image,
                )
                frame_number += 1

                now = monotonic()
                if now >= next_status_update:
                    elapsed = now - measurement_started
                    remaining = max(0, measurement_deadline - now)
                    print(
                        f"Acquisition: {frame_number} frames; "
                        f"{elapsed:.0f}s elapsed, {remaining:.0f}s remaining",
                        flush=True,
                    )
                    next_status_update = now + 30

                next_frame_time = max(next_frame_time + FRAME_INTERVAL_SECONDS, monotonic())
                frame_delay = next_frame_time - monotonic()
                if frame_delay > 0:
                    sleep(frame_delay)
        finally:
            injection_thread.join()

        if injection_errors:
            raise injection_errors[0]
        if arm_lift_started:
            arm.wait_for_home()
            arm_is_home = True
            

        print(f"Acquisition complete: {frame_number} measurement frames", flush=True)
    finally:
        try:
            if arm is not None and not arm_is_home:
                print("Returning arm to home position...", flush=True)
                arm.to_home()
        finally:
            if controller is not None:
                controller._close()
            print(f"Valve connection closed. Images saved in {run_dir}", flush=True)

    return run_dir


if __name__ == "__main__":
    run_time_lapse()