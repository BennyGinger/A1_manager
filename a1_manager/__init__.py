import importlib
import importlib.metadata
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


# Get the project root directory
dist = importlib.metadata.distribution("a1_manager")
_PROJECT_ROOT = Path(dist.locate_file(""))
CONFIG_DIR = _PROJECT_ROOT.joinpath("config")

# Set up logging
log_dir = _PROJECT_ROOT.joinpath('logs')
log_dir.mkdir(exist_ok=True)
log_file = log_dir.joinpath("a1_manager.log")

logging.basicConfig(
    level=logging.INFO, # Set the logging level to INFO, other options: DEBUG, WARNING, ERROR, CRITICAL
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(log_file, 
                            maxBytes=10_000_000,   # rotate after ~10 MB
                            backupCount=5)])       # keep 5 old files
    

# Limits the import to the following classes and functions
__all__ = ['A1Manager', 'run_autofocus', 'dmd_calibration', 'launch_dish_workflow']

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