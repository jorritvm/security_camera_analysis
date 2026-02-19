import time
import logging
import os
import sys
from datetime import datetime, tzinfo
from zoneinfo import ZoneInfo

# timers
class Timer:
    def __init__(self, name="Timer"):
        self.name = name
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.end_time = time.time()

    def elapsed(self):
        if self.start_time is None or self.end_time is None:
            return f"{self.name}: Timer not started or stopped."
        total_seconds = int(self.end_time - self.start_time)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{self.name}: {hours:02d}:{minutes:02d}:{seconds:02d}"



# logging
# # old version
# def setup_logging():
#     logging.basicConfig(
#         format='[%(asctime)s] %(message)s',
#         datefmt='%Y-%m-%dT%H:%M:%S',
#         level=logging.INFO
#     )

def log(s):
    logging.info(s)


# some stuff from pyutils


def setup_root_logger(log_level=logging.INFO,
                      with_logfile: bool = False,
                      log_folder_path: str = "logs/",
                      log_file_name: str = "app.log",
                      timestamp_log_file: bool = True) -> None:
    """Sets up the root logger with console and optional file handlers."""
    root_logger = logging.getLogger()

    # remove existing handlers so we can set up our own
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    if not root_logger.handlers:
        root_logger.setLevel(log_level)

        # Log console handler
        console_formatter = ColorizingFormatter("%(asctime)s-%(name)s-%(levelname)s: %(message)s",
                                                datefmt="%Y-%m-%dT%H:%M:%S")
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # Log file handler
        if with_logfile:
            # Handle file path
            os.makedirs(log_folder_path, exist_ok=True)
            # Prefix file name with timestamp
            if timestamp_log_file:
                # create a timestamp using get_current_date_and_time_str from the utils module in this folder
                date_str, time_str = get_current_date_and_time_str("%Y-%m-%d", "%H-%M-%S")
                prefix = f"{date_str}_{time_str}-"
                log_file_name = prefix + log_file_name
            log_file_path = os.path.join(log_folder_path, log_file_name)
            # Create and register the file logger
            file_formatter = IndentMultilineFormatter("%(asctime)s-%(name)s-%(levelname)s: %(message)s",
                                                      datefmt="%Y-%m-%dT%H:%M:%S")
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

        # Optional: prevent logs from being propagated to ancestor loggers
        root_logger.propagate = False

class IndentMultilineFormatter(logging.Formatter):
    """Makes sure multiline log messages are indented properly."""

    def format(self, record):
        original = super().format(record)
        if '\n' not in record.getMessage():
            return original
        # Find the length of the prefix before the message
        msg = record.getMessage()
        prefix = original.split(msg, 1)[0]
        indent = ' ' * len(prefix)
        lines = original.split('\n')
        return '\n'.join([lines[0]] + [indent + line for line in lines[1:]])

class ColorizingFormatter(IndentMultilineFormatter):
    """Adds color to log messages based on severity level."""
    COLORS = {
        'DEBUG': '\033[37m',  # White
        'INFO': '\033[0m',  # Reset
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[41m',  # Red background
        }
    RESET = '\033[0m'

    def format(self, record):
        msg = super().format(record)
        color = self.COLORS.get(record.levelname, self.RESET)
        return f"{color}{msg}{self.RESET}"

LOCAL_TZ = ZoneInfo("Europe/Brussels")

def get_current_date_and_time_str(date_format: str,
                                  time_format: str,
                                  tz: tzinfo = LOCAL_TZ) -> tuple[str, str]:
    """Return the current date and time as a tuple of strings formatted as desired."""
    return (get_current_date_str(date_format, tz), get_current_time_str(time_format, tz))

def get_current_date_str(date_format: str,
                         tz: tzinfo = LOCAL_TZ) -> str:
    """Return the current date as a string formatted as desired."""
    now_datetime = datetime.now(tz)
    return now_datetime.strftime(date_format)

def get_current_time_str(time_format: str,
                         tz: tzinfo = LOCAL_TZ) -> str:
    """Return the current time as a string formatted as desired."""
    now_datetime = datetime.now(tz)
    return now_datetime.strftime(time_format)
