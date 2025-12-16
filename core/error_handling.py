import functools
import logging
import traceback

# Configure logging
logging.basicConfig(
    filename='system_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def safe_execute(default_return=None):
    """
    Decorator to wrap functions in a try/except block.
    Logs errors and returns a default value on failure.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}")
                logger.debug(traceback.format_exc())
                return default_return
        return wrapper
    return decorator

class AppError(Exception):
    """Base custom exception class."""
    pass
