import importlib
import importlib.metadata
from pathlib import Path

from a1_manager.utils.logging_setup import configure_logging


# Get the project root directory
dist = importlib.metadata.distribution("a1_manager")
_PROJECT_ROOT = Path(dist.locate_file(""))
CONFIG_DIR = _PROJECT_ROOT.joinpath("config")

# Set up logging
configure_logging()
    

# Limits the import to the following classes and functions
__all__ = ['A1Manager', 'run_autofocus', 'dmd_calibration', 'launch_dish_workflow']

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # these lines are invisible at runtime, but IDEs index them
    from .a1manager       import A1Manager
    from .autofocus_main  import run_autofocus
    from .dmd_calibration import dmd_calibration
    from .dish_main       import launch_dish_workflow

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
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__() -> list[str]:
    """Override the default __dir__ to include the lazy loaded modules."""
    return __all__ + super().__dir__()