from rich.console import Console
from typing import Optional


class SingletonMeta(type):
    """A thread-safe implementation of Singleton pattern."""
    _instance: Optional['ConsoleSingleton'] = None

    def __call__(cls, *args, **kwargs) -> 'ConsoleSingleton':
        if cls._instance is None:
            cls._instance = super().__call__(*args, **kwargs)
        return cls._instance


class ConsoleSingleton(metaclass=SingletonMeta):
    """Singleton wrapper for Console to provide rich text output with consistent styling and log level control."""

    LOG_LEVELS = {
        "DEBUG": 10,
        "INFO": 20,
        "SUCCESS": 25,  # Adding SUCCESS level between INFO and WARNING
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50
    }

    def __init__(self, log_level: str = "WARNING"):
        self.console = Console()
        self.log_level = self.LOG_LEVELS.get(log_level.upper(), 30)  # Default to WARNING level

    def log(self, level: str, message: str) -> None:
        """
        General-purpose logging method with level control.

        Args:
            level (str): Log level of the message (e.g., 'INFO', 'WARNING', 'ERROR', 'SUCCESS').
            message (str): The message to log.
        """
        level_value = self.LOG_LEVELS.get(level.upper())
        if level_value is None:
            self.console.print(f"[magenta]Unknown log level: {level}[/magenta]")
            return

        # Only log messages with level >= the set log level
        if level_value >= self.log_level:
            color = self._get_color_for_level(level)
            self.console.print(f"[{color}]{level}: {message}[/{color}]")

    def set_log_level(self, log_level: str) -> None:
        """Sets the log level for the console output."""
        self.log_level = self.LOG_LEVELS.get(log_level.upper(), 30)  # Default to WARNING if level is invalid

    def _get_color_for_level(self, level: str) -> str:
        """Returns color code for each log level."""
        return {
            "DEBUG": "white",
            "INFO": "blue",
            "SUCCESS": "green",  # Green color for success messages
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold red",
        }.get(level.upper(), "blue")  # Default to blue if level not found

    # Convenience methods for specific log levels
    def debug(self, message: str) -> None:
        self.log("DEBUG", message)

    def info(self, message: str) -> None:
        self.log("INFO", message)

    def success(self, message: str) -> None:
        self.log("SUCCESS", message)

    def warning(self, message: str) -> None:
        self.log("WARNING", message)

    def error(self, message: str) -> None:
        self.log("ERROR", message)

    def critical(self, message: str) -> None:
        self.log("CRITICAL", message)
