import importlib
from pathlib import Path

from gem_logging import configure_logging


# Configure logging for the a1_manager package
configure_logging()

# Get the project root directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = _PROJECT_ROOT.joinpath("config")

# Limits the import to the following classes and functions
__all__ = ['A1Manager', 'run_autofocus', 'dmd_calibration', 'launch_dish_workflow', 'StageCoord']

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # these lines are invisible at runtime, but IDEs index them
    from .a1manager       import A1Manager
    from .autofocus_main  import run_autofocus
    from .dmd_calibration import dmd_calibration
    from .dish_main       import launch_dish_workflow
    from .utils.utility_classes import StageCoord

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
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__() -> list[str]:
    """Override the default __dir__ to include the lazy loaded modules."""
    return __all__ + super().__dir__()