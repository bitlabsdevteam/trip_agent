import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

class ProjectLogger:
    """Centralized logging configuration for the project."""
    
    _loggers = {}
    _initialized = False
    
    @classmethod
    def setup_logging(cls, log_level=logging.INFO, log_dir="logs"):
        """Setup logging configuration for the entire project.
        
        Args:
            log_level: Logging level (default: INFO)
            log_dir: Directory to store log files (default: "logs")
        """
        if cls._initialized:
            return
            
        # Create logs directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear any existing handlers
        root_logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler for all logs
        all_logs_file = log_path / "application.log"
        file_handler = logging.handlers.RotatingFileHandler(
            all_logs_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Error-only file handler
        error_logs_file = log_path / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_logs_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
        
        # Debug file handler (only when debug level is enabled)
        if log_level <= logging.DEBUG:
            debug_logs_file = log_path / "debug.log"
            debug_handler = logging.handlers.RotatingFileHandler(
                debug_logs_file,
                maxBytes=20*1024*1024,  # 20MB
                backupCount=2
            )
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(detailed_formatter)
            root_logger.addHandler(debug_handler)
        
        cls._initialized = True
        
        # Log initialization
        logger = cls.get_logger("ProjectLogger")
        logger.info("Logging system initialized successfully")
        logger.info(f"Log directory: {log_path.absolute()}")
        logger.info(f"Log level: {logging.getLevelName(log_level)}")
    
    @classmethod
    def get_logger(cls, name):
        """Get a logger instance for a specific module/component.
        
        Args:
            name: Logger name (typically module name)
            
        Returns:
            logging.Logger: Configured logger instance
        """
        if not cls._initialized:
            cls.setup_logging()
            
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(name)
            
        return cls._loggers[name]
    
    @classmethod
    def log_function_call(cls, logger, func_name, *args, **kwargs):
        """Log function entry with parameters.
        
        Args:
            logger: Logger instance
            func_name: Function name
            *args: Function arguments
            **kwargs: Function keyword arguments
        """
        args_str = ", ".join([str(arg) for arg in args])
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        params = ", ".join(filter(None, [args_str, kwargs_str]))
        logger.debug(f"Entering {func_name}({params})")
    
    @classmethod
    def log_function_exit(cls, logger, func_name, result=None, execution_time=None):
        """Log function exit with result and execution time.
        
        Args:
            logger: Logger instance
            func_name: Function name
            result: Function result (optional)
            execution_time: Execution time in seconds (optional)
        """
        msg = f"Exiting {func_name}"
        if execution_time is not None:
            msg += f" (took {execution_time:.3f}s)"
        if result is not None:
            msg += f" -> {type(result).__name__}"
        logger.debug(msg)
    
    @classmethod
    def log_error_with_context(cls, logger, error, context=None, session_id=None):
        """Log error with additional context information.
        
        Args:
            logger: Logger instance
            error: Exception or error message
            context: Additional context information
            session_id: Session ID for tracking
        """
        error_msg = f"Error occurred: {str(error)}"
        
        if session_id:
            error_msg += f" [Session: {session_id}]"
            
        if context:
            error_msg += f" [Context: {context}]"
            
        if isinstance(error, Exception):
            logger.error(error_msg, exc_info=True)
        else:
            logger.error(error_msg)

# Convenience function to get logger
def get_logger(name=None):
    """Get a logger instance.
    
    Args:
        name: Logger name (defaults to calling module name)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return ProjectLogger.get_logger(name)

# Initialize logging on import
ProjectLogger.setup_logging()