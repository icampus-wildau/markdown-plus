from __future__ import annotations
from functools import wraps

import logging

from rich.console import Console
from rich.progress import Progress, TaskID

console = Console()

logger = logging.getLogger(__name__)


class Logger:
    @staticmethod
    def get_console():
        global console
        return console

    @staticmethod
    def setup_logger(level: int = logging.INFO):
        logger = logging.getLogger("mdplus")
        logger.setLevel(level)
        logger.addHandler(ConsoleLogger())

    @staticmethod
    def get_plain_text(message):
        """Returns a plain text without any rich formatting"""
        return Logger.get_console().render_str(message).plain

    @staticmethod
    def print_exception_message(exception: Exception, include_exception_name=True):
        """
        Prints an exception message to the console.

        Parameters
        ----------
        exception: Exception
            The exception to print
        include_exception_name: bool
            If True, the exception name will be included in the message
        """
        if include_exception_name:
            msg = f"[bold red]{type(exception).__name__}: [/bold red][red][/red]: {exception}"
        else:
            msg = f"[bold red]{exception}[/bold red]"
        Logger.get_console().print(msg)


class RichFormatter(logging.Formatter):
    def __init__(self, compact: bool = False):
        super().__init__()
        self.base_format = "[%(levelname)s] %(message)s [%(asctime)s] (%(name)s - %(filename)s:%(lineno)d)"
        self.compact_format = "[%(levelname)s] %(message)s"
        self.raw_format = "%(message)s"

        f = self.compact_format if compact else self.base_format

        self.colored_formats = {
            logging.DEBUG: "[grey]" + f,
            logging.INFO: "[grey]" + (self.raw_format if compact else f),
            logging.WARNING: "[yellow]" + f,
            logging.ERROR: "[red]" + f,
            logging.CRITICAL: "[bold red]" + f,
        }

        self.formatters = {
            logging.DEBUG: logging.Formatter(self.colored_formats[logging.DEBUG]),
            logging.INFO: logging.Formatter(self.colored_formats[logging.INFO]),
            logging.WARNING: logging.Formatter(self.colored_formats[logging.WARNING]),
            logging.ERROR: logging.Formatter(self.colored_formats[logging.ERROR]),
            logging.CRITICAL: logging.Formatter(self.colored_formats[logging.CRITICAL]),
        }

    def format(self, record: logging.LogRecord):
        formatter = self.formatters[record.levelno]
        return formatter.format(record)


class ConsoleLogger(logging.StreamHandler):
    def __init__(self):
        super().__init__()
        global console
        self.console = console

        self.setFormatter(RichFormatter(compact=True))

    def emit(self, record):
        try:
            msg = self.format(record)
            # TODO add real logging
            self.console.print(msg)
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
