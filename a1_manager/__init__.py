import importlib
from pathlib import Path


# Get the project root directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = _PROJECT_ROOT.joinpath("config")

# Limits the import to the following classes and functions
__all__ = ['A1Manager', 'run_autofocus', 'dmd_calibration', 'launch_dish_workflow', 'StageCoord', 'load_config_file', 'WellCircleCoord', 'WellSquareCoord']

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # these lines are invisible at runtime, but IDEs index them
    from .a1manager       import A1Manager
    from .autofocus_main  import run_autofocus
    from .dmd_calibration import dmd_calibration
    from .dish_main       import launch_dish_workflow
    from .utils.utility_classes import StageCoord, WellCircleCoord, WellSquareCoord
    from .utils.json_utils import load_config_file

# lazy importing of the modules
def __getattr__(name: str) -> object:
    """Lazy import of the module."""
    if name == "A1Manager":
        return importlib.import_module(".a1manager", __name__).A1Manager
    if name == "run_autofocus":
        return importlib.import_module(".autofocus_main", __name__).run_autofocus
    if name == "dmd_calibration":
        return importlib.import_module(".dmd_calibration", __name__).dmd_calibration
    if name == "launch_dish_workflow":
        return importlib.import_module(".dish_main", __name__).launch_dish_workflow
    if name == "StageCoord":
        return importlib.import_module(".utils.utility_classes", __name__).StageCoord
    if name == "load_config_file":
        return importlib.import_module(".utils.json_utils", __name__).load_config_file
    if name == "save_config_file":
        return importlib.import_module(".utils.json_utils", __name__).save_config_file
    if name == "WellCircleCoord":
        return importlib.import_module(".utils.utility_classes", __name__).WellCircleCoord
    if name == "WellSquareCoord":
        return importlib.import_module(".utils.utility_classes", __name__).WellSquareCoord
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__() -> list[str]:
    """Override the default __dir__ to include the lazy loaded modules."""
    return __all__ + super().__dir__()