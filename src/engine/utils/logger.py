import logging
import sys

def setup_logger(name: str = "HeroEngine", level: int = logging.INFO) -> logging.Logger:
    """Setup and configure a unified logger output to console.

    Args:
        name: Name of the logger.
        level: Logging level (e.g. logging.DEBUG, logging.INFO).

    Returns:
        logging.Logger: Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger
