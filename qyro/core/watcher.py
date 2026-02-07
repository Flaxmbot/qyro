import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console

console = Console()

class QyroHandler(FileSystemEventHandler):
    """Handles file system events for Qyro files."""
    
    def __init__(self, callback, file_path: Path):
        self.callback = callback
        self.file_path = file_path.resolve()
        self.last_triggered = 0
        self.debounce_seconds = 1.0

    def on_modified(self, event):
        try:
            # Check if the modified file matches our target file
            if Path(event.src_path).resolve() == self.file_path:
                current_time = time.time()
                if current_time - self.last_triggered > self.debounce_seconds:
                    self.last_triggered = current_time
                    self.callback()
        except Exception as e:
            console.print(f"[red]Error in file watcher handler: {e}[/]")

class QyroWatcher:
    """Watches a specific file for changes and triggers a callback."""
    
    def __init__(self, file_path: Path, callback):
        self.file_path = file_path
        self.callback = callback
        self.observer = Observer()

    def start(self):
        """Start watching the file."""
        handler = QyroHandler(self.callback, self.file_path)
        # Watch the directory containing the file
        self.observer.schedule(handler, str(self.file_path.parent), recursive=False)
        self.observer.start()
        console.print(f"[bold green]👀 Watching for changes in {self.file_path.name}...[/]")

    def stop(self):
        """Stop watching."""
        if self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
