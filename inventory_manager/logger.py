import logging
import os

def setup_logger():
    """
    Configures and returns the system logger.
    Logs are written to 'inventory.log' in the project root.
    """
    logger = logging.getLogger("inventory_manager")
    
    # If logger already has handlers, don't duplicate them
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)

    # Define log format
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )

    # File Handler - logs everything (DEBUG and above)
    log_file = "inventory.log"
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # If writing to file fails (e.g. permissions), print a warning to stderr
        print(f"Warning: Could not create log file: {e}")

    # Prevent logs from propagating to the root logger to avoid console clutter
    logger.propagate = False

    return logger

# Initialize the logger instance
logger = setup_logger()
