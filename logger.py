import logging
import sys

from pathlib import Path
from dataclasses import fields
from datetime import datetime
from logger_template import LoggerTemplate, LOGGER_NAME


def set_logger(**kwargs) -> logging.Logger:
    """
    Setup logger for the project.

    Keyword Args:
        enable_logger (bool): Turn ON/OFF logging. If False, all arguments below will be ignored.
        enable_logfile (bool): Turn ON/OFF logging in file.
        logger (logging.Logger): User defined logger. Overrides all logger presets.
        logfile_path (pathlib.Path): Log files storage path. It creates a folder next to the script by default.
        logfile_name (pathlib.Path): Log file name. It is '__DD.MM.YYYY__HH.00__.log' by default.
        logfile_level (int): File logging level.
        log_std_level (int): Console logging level.
        show_std_traceback (bool): Turn ON/OFF console traceback.

    Returns:
        logging.Logger: Logger object.
    """

    logger_template = LoggerTemplate()
    for key, value in kwargs.items():
        if key in [field.name for field in fields(logger_template)]:
            setattr(logger_template, key, value)

    if not isinstance(logger_template.logger, logging.Logger):
        logger_template.logger = logging.getLogger(LOGGER_NAME)
    else:  # means logger has been overriden by user
        return logger_template.logger

    logger = logger_template.logger

    if not logger_template.enable_logger:
        logger.setLevel(logging.CRITICAL + 1)
    else:
        logger.setLevel(logging.DEBUG)

        std_formatter = StdFormatter()
        std_formatter.set_exceptions_enabled(logger_template.show_std_traceback)
        std_handler = logging.StreamHandler(sys.stdout)
        std_handler.setLevel(logger_template.log_std_level)
        std_handler.setFormatter(std_formatter)
        logger.addHandler(std_handler)

        if not logger_template.enable_logfile:
            logger.debug(f'Logging without file')
        else:
            file_formatter = FileFormatter()
            Path.mkdir(Path(logger_template.logfile_path), parents=True, exist_ok=True)
            log_file_path = Path(logger_template.logfile_path) / Path(str(logger_template.logfile_name))
            file_handler = FirstRowFileHandler(log_file_path)
            file_handler.setLevel(logger_template.logfile_level)
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            logger.debug(f'Logging to the file [{log_file_path}]')

    return logger


class FirstRowFileHandler(logging.FileHandler):
    """
    Handler for the first row of the file.
    """

    def __init__(self, filename, *args):
        super().__init__(filename, *args)
        self.first_run = True
        self.filename = filename
        self.separator = f"{'=' * 7} API Launch {datetime.now().strftime('[%d.%m.%Y %H:%M:%S]')} {'=' * 70}"

    def emit(self, record):
        if self.first_run:
            self.stream.write(f'\n\n\n{self.separator}\n\n\n')
        self.first_run = False
        super().emit(record)


class FileFormatter(logging.Formatter):
    """
    File formatter. Overrides exception and message formats.
    """

    def __init__(self):
        logging.Formatter.__init__(self)
        self.is_last_msg_exception = False

    def format(self, record):
        self._style._fmt = f"[%(asctime)s] %(levelname)-8s [%(filename)s/%(funcName)s:%(lineno)s]  %(message)s"
        return super().format(record)

    def formatException(self, exc_info) -> str:
        self.is_last_msg_exception = True
        return '\n' + super().formatException(exc_info)

    def formatMessage(self, record) -> str:
        if self.is_last_msg_exception:
            self.is_last_msg_exception = False
            return '\n' + super().formatMessage(record)
        return super().formatMessage(record)


class StdFormatter(logging.Formatter):
    """
    Console formatter. Overrides exception and message formats.
    """

    _enable_exceptions: bool = False

    def format(self, record):

        color = {
            logging.CRITICAL: (31, 31),
            logging.ERROR: (31, 31),
            logging.FATAL: (31, 31),
            logging.WARNING: (33, 33),
            logging.DEBUG: (36, 37),
            logging.INFO: (32, 32)
        }.get(record.levelno, 0)
        self._style._fmt = f"\033[37m[%(asctime)s]\033[0m \033[{color[0]}m%(levelname)-8s\033[0m \033[{color[1]}m%(message)s\033[0m"
        return super().format(record)

    def set_exceptions_enabled(self, enable: bool):
        self._enable_exceptions = enable

    def formatException(self, exc_info) -> str:
        if self._enable_exceptions:
            return super().formatException(exc_info)
        return ''
