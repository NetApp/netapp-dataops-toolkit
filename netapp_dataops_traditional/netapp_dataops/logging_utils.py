import logging

def setup_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """
    Sets up a logger with a console handler.

    Args:
        name (str): The name of the logger.
        level (int): The logging level. Default is logging.DEBUG.

    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.hasHandlers():
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger