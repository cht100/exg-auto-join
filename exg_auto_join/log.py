from __future__ import annotations

import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import DEFAULT_LOG_FILE

_LOGGER_NAME = "exg_auto_join"
_LOGGER = logging.getLogger(_LOGGER_NAME)


def _rotate_on_start(log_file: Path, backup_count: int = 3) -> None:
    """每次启动时把旧日志向后滚动一份，让新日志从空文件开始。"""
    if not log_file.exists() or log_file.stat().st_size == 0:
        return

    for index in range(backup_count, 1, -1):
        src = Path(f"{log_file}.{index - 1}")
        dst = Path(f"{log_file}.{index}")
        if dst.exists():
            dst.unlink()
        if src.exists():
            src.rename(dst)

    first_backup = Path(f"{log_file}.1")
    if first_backup.exists():
        first_backup.unlink()
    log_file.rename(first_backup)


def configure_logging(
    log_file: Path = DEFAULT_LOG_FILE,
    max_bytes: int = 1_000_000,
    backup_count: int = 3,
) -> None:
    """配置控制台 + 滚动文件双输出；每次启动自动滚动旧日志。"""
    _rotate_on_start(Path(log_file), backup_count)
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    _LOGGER.setLevel(logging.INFO)
    _LOGGER.propagate = False
    for handler in list(_LOGGER.handlers):
        _LOGGER.removeHandler(handler)

    formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%H:%M:%S")

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    _LOGGER.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    _LOGGER.addHandler(console_handler)


def log(message: str) -> None:
    if _LOGGER.handlers:
        _LOGGER.info(message)
        return

    # 尚未配置时至少保证控制台可读
    stamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{stamp}] {message}", file=sys.stdout, flush=True)
