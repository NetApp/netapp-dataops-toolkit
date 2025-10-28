import logging

class UserFriendlyFormatter(logging.Formatter):
    """Custom formatter that suppresses stack traces for user-facing messages."""
    
    def format(self, record):
        if record.levelno >= logging.ERROR and record.exc_info:
            # Prevents stack trace from being displayed
            record.exc_info = None
            record.exc_text = None
            record.stack_info = None
        return super().format(record)

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
        formatter = UserFriendlyFormatter('%(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger