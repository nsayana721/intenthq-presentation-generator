"""Logging configuration."""

import logging
from pathlib import Path
from config import settings
from datetime import datetime


def setup_logging(log_level=logging.INFO):
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (default: INFO)
    """
    # Create logs directory
    settings.logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Log file path
    log_file = settings.logs_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    # Set specific log levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    logging.info("Logging initialized")