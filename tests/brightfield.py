from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from a1_manager import A1Manager

# Same filter positions as the 'bf' entry in config/optical_configuration.json
BF_TURRET = 0
BF_WHEEL = 0
BF_LIGHT_PATH = 1


@contextmanager
def brightfield(a1_manager: A1Manager, exposure_ms: float = 50) -> Iterator[None]:
    """
    Brightfield focusing with the LED on the needle: only the filter turret/wheel, light path and
    camera exposure are set. No lamp is touched.
    """
    a1_manager.core.set_property("FilterTurret1", "State", BF_TURRET)
    a1_manager.core.set_property("FilterWheel1", "State", BF_WHEEL)
    a1_manager.nikon.set_light_path(BF_LIGHT_PATH)
    a1_manager.camera.set_camera_exposure(exposure_ms)
    try:
        yield
    finally:
        # The hardware no longer matches the cached lamp/camera/light-path state, so force a full re-apply
        a1_manager.lamp.clear_lamp_cache()
        a1_manager._cached_oc_state["exposure_ms"] = None
        a1_manager._cached_oc_state["light_path"] = None
