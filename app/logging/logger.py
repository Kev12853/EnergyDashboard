# Python's built-in logging module.
# Provides Logger, INFO, WARNING, ERROR, etc.
import logging

# Provides RotatingFileHandler, which writes logs to a file
# and automatically starts a new file when the current file
# reaches the configured size.
from logging.handlers import RotatingFileHandler

# Import the directory where log files should be stored.
# The actual location is defined centrally in project_paths.py.
from app.config.project_paths import LOG_DIR


def setup_logger(name: str) -> logging.Logger:
    """
    Create and configure a logger for the specified service.

    name:
        The name of the logger, for example "Octopus Service".

    Returns:
        A configured logging.Logger object.
    """

    # Get the logger with this name.
    #
    # logging.getLogger() is effectively a registry. If a logger
    # with this name already exists, Python returns the existing
    # logger rather than creating a completely new one.
    logger = logging.getLogger(name)

    # Check whether this logger has already been configured.
    #
    # This is important because setup_logger() might be called
    # more than once. Without this check, every call would add
    # another file handler and console handler, causing duplicate
    # log messages.
    if logger.handlers:
        return logger

    # Set the minimum severity that this logger will process.
    #
    # INFO means:
    #   DEBUG    -> ignored
    #   INFO     -> logged
    #   WARNING  -> logged
    #   ERROR    -> logged
    #   CRITICAL -> logged
    logger.setLevel(logging.INFO)

    # Make sure the log directory exists.
    #
    # parents=True:
    #     Create any missing parent directories as well.
    #
    # exist_ok=True:
    #     Don't raise an error if the directory already exists.
    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Define the format used for every log message.
    #
    # %(asctime)s  -> date/time
    # %(levelname)s -> INFO, WARNING, ERROR, etc.
    # %(name)s     -> logger name, e.g. "Octopus Service"
    # %(message)s  -> the actual message
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    # Create the file handler.
    #
    # This sends log messages to:
    #
    #     LOG_DIR / "<logger name>.log"
    #
    # For example:
    #
    #     logs/Octopus Service.log
    #
    # maxBytes:
    #     Maximum size of one log file: 5 MB.
    #
    # backupCount:
    #     Keep 5 old log files when rotation occurs.
    #
    # encoding:
    #     Store the file as UTF-8.
    file_handler = RotatingFileHandler(
        LOG_DIR / f"{name}.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )

    # Apply our log format to the file handler.
    file_handler.setFormatter(formatter)

    # Create a console handler.
    #
    # This sends log messages to the console/terminal as well
    # as to the log file.
    console_handler = logging.StreamHandler()

    # Apply the same format to console messages.
    console_handler.setFormatter(formatter)

    # Attach the file handler to our logger.
    #
    # Messages sent to this logger will now be written to the
    # rotating log file.
    logger.addHandler(file_handler)

    # Attach the console handler.
    #
    # Messages will also appear in the terminal.
    logger.addHandler(console_handler)

    # Prevent this logger's messages from being passed on to
    # the root logger.
    #
    # Without this, another logging configuration higher up the
    # hierarchy could cause messages to appear a second time.
    logger.propagate = False

    # Write a message confirming where this logger is writing.
    #
    # %s is handled by the logging system rather than using an
    # f-string.
    logger.warning(
        "Logging to %s",
        file_handler.baseFilename,
    )

    # Return the fully configured logger to the caller.
    return logger
