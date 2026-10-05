from __future__ import annotations

from datetime import datetime
from pathlib import Path
from threading import Event, Thread
from time import monotonic, sleep

from tifffile import imwrite

from a1_manager import A1Manager
from a1_manager.microscope_hardware.nanopick.devices.marZ import MarZ
from a1_manager.microscope_hardware.nanopick.devices.valve import PICController, VALVE_2_TIME


DISH = "96well"
OBJECTIVE = "10x"
OPTICAL_CONFIGURATION = "RFP"
FILTER_WHEEL = 4

EXPOSURE_MS = 200
VALVE_PORT = "COM8"
NEEDLE_SIZE_UM = 50
PRESSURE_BAR = 0.30
INJECTION_VOLUME_UL = 10
MIXING_CYCLES = 200
MIXING_CYCLE_INTERVAL_SECONDS = 2.0
BASELINE_FRAME_COUNT = 5

DURATION_SECONDS = 5 * 60
OUTPUT_ROOT = Path(r"D:\Zsuzsi\Diffusion experiments\20261001_LTB4_c1913b_Diffusion_96well")


def run_time_lapse() -> Path:
    run_dir = OUTPUT_ROOT / datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=False)
    print(f"Run folder: {run_dir}", flush=True)
    print("Connecting to microscope and valve...", flush=True)

    a1_manager = A1Manager(
        objective=OBJECTIVE,
        exposure_ms=EXPOSURE_MS,
        lamp_name="pE-800",
        focus_device="PFSOffset",
    )
    controller = PICController(
        needle_size=NEEDLE_SIZE_UM,
        pressure=PRESSURE_BAR,
        port=VALVE_PORT,
    )
    arm: MarZ | None = None
    arm_is_home = False

    try:
        print("Preparing arm and RFP imaging...", flush=True)
        arm = MarZ(core=a1_manager.core, dish=DISH)
        a1_manager.oc_settings(OPTICAL_CONFIGURATION, exposure_ms=EXPOSURE_MS)
        a1_manager.core.set_property("FilterWheel1", "State", FILTER_WHEEL)
        a1_manager.set_stage_position(a1_manager.nikon.get_stage_position())

        print(
            "Check RFP focus in Micro-Manager and adjust if needed; press Enter to capture baseline.",
            flush=True,
        )
        input()

        print(f"Capturing {BASELINE_FRAME_COUNT} baseline images...", flush=True)
        for frame_number in range(BASELINE_FRAME_COUNT):
            image = a1_manager.snap_image(dmd_exposure_sec=EXPOSURE_MS / 1000)
            imwrite(run_dir / f"baseline_{frame_number:06d}.tif", image)
            print(f"Baseline: {frame_number + 1}/{BASELINE_FRAME_COUNT}", flush=True)


        print(f"Moving arm to calibration position; starting {MIXING_CYCLES} injection cycles...", flush=True)
        arm.to_calibration()
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

        injection_thread = Thread(target=run_injection_cycles, name="valve-injection")
        injection_thread.start()
        print("Capturing continuously during injection...", flush=True)
        post_injection_deadline: float | None = None
        next_status_update = injection_started + 30
        frame_number = 0
        try:
            while True:
                if injection_errors:
                    break

                now = monotonic()
                if injection_done.is_set():
                    if post_injection_deadline is None:
                        print("Injection complete; lifting needle...", flush=True)
                        arm.to_home()
                        arm_is_home = True
                        post_injection_deadline = monotonic() + DURATION_SECONDS
                        print("Injection complete; continuing time-lapse for five minutes...", flush=True)
                    elif now >= post_injection_deadline:
                        break

                image = a1_manager.snap_image(dmd_exposure_sec=EXPOSURE_MS / 1000)
                phase = "injection" if post_injection_deadline is None else "frame"
                imwrite(run_dir / f"{phase}_{frame_number:06d}.tif", image)
                frame_number += 1

                now = monotonic()
                if now >= next_status_update:
                    if post_injection_deadline is None:
                        print(f"Acquisition: {frame_number} frames; injection is running", flush=True)
                    else:
                        elapsed = DURATION_SECONDS - max(0, post_injection_deadline - now)
                        remaining = max(0, post_injection_deadline - now)
                        print(
                            f"Post-injection imaging: {frame_number} frames; "
                            f"{elapsed:.0f}s elapsed, {remaining:.0f}s remaining",
                            flush=True,
                        )
                    next_status_update = now + 30
        finally:
            injection_thread.join()

        if injection_errors:
            raise injection_errors[0]

        print(f"Acquisition complete: {frame_number} injection/post-injection frames", flush=True)
    finally:
        try:
            if arm is not None and not arm_is_home:
                print("Returning arm to home position...", flush=True)
                arm.to_home()
        finally:
            controller._close()
            print(f"Valve connection closed. Images saved in {run_dir}", flush=True)

    return run_dir


if __name__ == "__main__":
    run_time_lapse()