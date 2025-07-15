import logging
import sys
from logging.handlers import TimedRotatingFileHandler

def setup_logging(log_level: str = "INFO"):
    """Set up logging for the application."""
    
    # Define a filter that adds session_id to records if it's missing
    class SessionIdFilter(logging.Filter):
        def filter(self, record):
            if not hasattr(record, 'session_id'):
                record.session_id = 'N/A'
            return True

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # Create a formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - [%(session_id)s] - %(message)s'
    )
    
    # Create a console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Create a rotating file handler
    file_handler = TimedRotatingFileHandler(
        "logs/conversation.log", when="midnight", interval=1, backupCount=7
    )
    file_handler.setFormatter(formatter)
    
    # Add the filter to both handlers
    console_handler.addFilter(SessionIdFilter())
    file_handler.addFilter(SessionIdFilter())
    
    # Add handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logging.info("Logging configured.") 