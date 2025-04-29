import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def find_project_root() -> Path:
    """
    Find the project root directory from where the script is run.
    """
    cwd = Path.cwd()
    for d in (cwd, *cwd.parents):
        if (d / ".git").is_dir() or (d / "pyproject.toml").exists():
            return d
    return cwd

def configure_logging(log_folder: str = "logs", log_filename: str = "a1_manager.log", max_bytes: int = 10_000_000, backup_count: int = 5, level: int = logging.INFO) -> Path:
    """
    Configure logging for the project.
    Args:
        log_folder (str): Folder to save the log files.
        log_filename (str): Name of the log file.
        max_bytes (int): Maximum size of the log file before rotation.
        backup_count (int): Number of backup files to keep.
        level (int): Logging level. Default is logging.INFO.
    Returns:
        pathlib.Path: Path to the log file.
    """
    # Get the project root directory
    project_root = find_project_root()
    log_dir = project_root / log_folder
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / log_filename
    
    # create a custom logger
    fmt = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt, datefmt=datefmt)

    # create your handlers
    stream_h = logging.StreamHandler()
    file_h   = RotatingFileHandler(log_file, maxBytes=max_bytes,
                                   backupCount=backup_count,
                                   encoding="utf-8")

    # apply shared settings
    for h in (stream_h, file_h):
        h.setLevel(level)
        h.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)

    # only add once
    if not any(isinstance(h, RotatingFileHandler) and Path(h.baseFilename) == log_file
               for h in root.handlers):
        root.addHandler(stream_h)
        root.addHandler(file_h)

    return log_file
