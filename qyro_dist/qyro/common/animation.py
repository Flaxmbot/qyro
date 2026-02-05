"""
Animation utilities for Qyro - The Universal Polyglot Runtime
Provides animated console output, headers, and loading indicators.
"""

from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live
import pyfiglet
from art import tprint
import time


class AnimatedConsole:
    """A console class with animation capabilities."""
    
    def __init__(self):
        self.console = Console()
    
    def animate_ascii(self, text, font="slant", style="bold cyan"):
        """Display animated ASCII art text."""
        ascii_art = pyfiglet.figlet_format(text, font=font)
        header_text = Text(ascii_art, style=style)
        self.console.print(header_text)
    
    def animate_text(self, text, delay=0.05):
        """Animate text character by character."""
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()  # newline at the end
    
    def animate_progress(self, message="Processing", duration=3):
        """Show an animated progress indicator."""
        spinner = Spinner("clock", style="cyan")
        text = Text(message, style="bold yellow")
        panel = Panel(spinner, title=text, border_style="yellow")
        
        with Live(panel, refresh_per_second=20):
            time.sleep(duration)
        
        self.console.print(f"[bold green]{message} complete![/bold green]")
    
    def print_header(self, title="Qyro", subtitle="Universal Polyglot Runtime"):
        """Print an animated header with title and subtitle."""
        self.animate_ascii(title, style="bold cyan")
        subtitle_text = Text(f"\n{subtitle}", style="bold magenta")
        self.console.print(subtitle_text)
        
        # Add a decorative line
        self.console.print(Panel("", title="[bold green]Initializing Qyro Runtime[/bold green]", expand=False))


# Global instance for convenience
animated_console = AnimatedConsole()


def print_animated_header():
    """Print the Qyro header with animated ASCII art."""
    animated_console.print_header()


def show_loading_animation(message="Loading"):
    """Show a rich loading animation."""
    console = Console()
    spinner = Spinner("dots", style="green")
    text = Text(message, style="bold blue")
    panel = Panel(spinner, title=text, border_style="blue")
    
    with Live(panel, refresh_per_second=20):
        time.sleep(2)  # Simulate work
    
    console.print(f"[bold green]{message} complete![/bold green]")


if __name__ == "__main__":
    # Demo of animation capabilities
    ac = AnimatedConsole()
    ac.print_header()
    ac.animate_progress("Demo Animation", 2)