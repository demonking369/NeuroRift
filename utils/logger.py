"""
Logger utility for NeuroRift
"""

# ╔══════════════════════════════════════════════════════════╗
# ║ NeuroRift - Built with Blood by DemonKing369.0 👑        ║
# ║ GitHub: https://github.com/Arunking9                     ║
# ║ AI-Powered Security Framework for Bug Bounty Warriors ⚔️║
# ╚══════════════════════════════════════════════════════════╝

import logging
import sys
from pathlib import Path
from rich.logging import RichHandler
import os
from datetime import datetime


def setup_logger(name: str, log_dir: str = None) -> logging.Logger:
    """Set up a logger with the given name."""
    if log_dir is None:
        log_dir = os.path.join(os.path.expanduser("~"), ".neurorift", "logs")

    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create handlers
    log_file = os.path.join(log_dir, f"{name}.log")
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()

    # Create formatters and add it to handlers
    log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(log_format)
    console_handler.setFormatter(log_format)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
