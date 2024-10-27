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
    """Singleton wrapper for Console to provide rich text output with consistent styling across the application."""

    def __init__(self):
        self.console = Console()

    def print_info(self, message: str) -> None:
        """Prints informational messages in blue."""
        self.console.print(f"[blue]{message}[/blue]")

    def print_warning(self, message: str) -> None:
        """Prints warning messages in yellow."""
        self.console.print(f"[yellow]{message}[/yellow]")

    def print_error(self, message: str) -> None:
        """Prints error messages in red."""
        self.console.print(f"[red]{message}[/red]")

    def print_success(self, message: str) -> None:
        """Prints success messages in green."""
        self.console.print(f"[green]{message}[/green]")
