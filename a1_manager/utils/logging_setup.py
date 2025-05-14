import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union


def configure_logging(*, log_file: Optional[Union[str, Path]] = None, max_bytes: int = 10_000_000, backup_count: int = 5, level: int = logging.INFO) -> logging.Logger:
    """
    Configure root logging.  By default logs only to console.
    If log_file is provided, adds a RotatingFileHandler there.

    Args:
        log_file: Path to the log file.  If None, no file logging.
        max_bytes: Max bytes for rotation.
        backup_count: Number of rotated files to keep.
        level: Logging level.

    Returns:
        The root logger.
    """
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handlers = [logging.StreamHandler()]

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_h = RotatingFileHandler(
            filename=str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8")
        handlers.append(file_h)

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=datefmt,
        handlers=handlers)

    return logging.getLogger()
