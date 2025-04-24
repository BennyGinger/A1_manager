# Import the main classes and functions at the pkg level
# Usage:
# from a1_manager import A1Manager, do_autofocus, dmd_calibration
# or import a1_manager --> a1_manager.A1Manager, a1_manager.do_autofocus, a1_manager.dmd_calibration

# from .main import A1Manager
# from .autofocus_main import run_autofocus
# from .dmd_calibration import dmd_calibration


# Limits the import to the following classes and functions
__all__ = ['A1Manager', 'run_autofocus', 'dmd_calibration']

# lazy importing of the modules
import importlib

def __getattr__(name: str) -> object:
    """Lazy import of the module."""
    if name == "A1Manager":
        return importlib.import_module(".main", __name__).A1Manager
    if name == "run_autofocus":
        return importlib.import_module(".autofocus_main", __name__).run_autofocus
    if name == "dmd_calibration":
        return importlib.import_module(".dmd_calibration", __name__).dmd_calibration
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__() -> list[str]:
    """Override the default __dir__ to include the lazy loaded modules."""
    return __all__ + super().__dir__()