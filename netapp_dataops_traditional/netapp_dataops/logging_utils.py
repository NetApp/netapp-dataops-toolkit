import logging

class UserFriendlyFormatter(logging.Formatter):
    """Custom formatter that suppresses stack traces for user-facing messages."""
    
    def format(self, record):
        try:
            # For ERROR and CRITICAL levels, only show the message without stack trace
            if record.levelno >= logging.ERROR:
                # Clear exc_info to prevent stack trace from being displayed
                record.exc_info = None
                record.exc_text = None
                record.stack_info = None
                
                # Handle cases where args don't match the message format
                if record.args:
                    try:
                        # Try to format normally first
                        record.getMessage()
                    except (TypeError, ValueError):
                        # If formatting fails, combine message and args manually
                        if len(record.args) == 1:
                            record.msg = str(record.msg) + str(record.args[0])
                        else:
                            record.msg = str(record.msg) + ' '.join(str(arg) for arg in record.args)
                        record.args = None
            
            return super().format(record)
        except Exception:
            # Fallback: return a simple error message
            return f"Error occurred: {getattr(record, 'msg', 'Unknown error')}"


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