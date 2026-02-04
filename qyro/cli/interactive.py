"""
Interactive CLI for Qyro (qyro init).
Uses 'rich' for beautiful output and 'questionary' for interactive prompts.
"""
import os
import json
import sys
import time
import shutil
from typing import List, Dict, Any

# Try to import rich/questionary, fallback to basic input if missing
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.prompt import Prompt, Confirm
    from rich.live import Live
    from rich.layout import Layout
    from rich.align import Align
    from rich import print as rprint
    from rich.style import Style
    import questionary
    HAS_UI_LIBS = True
except ImportError:
    HAS_UI_LIBS = False
    import colorama
    colorama.init()

def animate_banner(console):
    """Display a typing animation for the Qyro banner."""
    title = r"""
  _   _ ________   __  _______  _____
  | \ | |  ____\ \ / / |__   __||_   _|
  |  \| | |__   \ V /     | |     | |
  | . ` |  __|   > <      | |     | |
  | |\  | |____ / . \     | |    _| |_
  |_| \_|______/_/ \_\    |_|   |_____|
"""

    # Typing effect for "Initializing Qyro Runtime..."
    text = Text("")
    with Live(Align.center(text), refresh_per_second=15, console=console) as live:
        time.sleep(0.5)
        msg = "Initializing Qyro Runtime Environment..."
        for i in range(len(msg) + 1):
            text = Text(msg[:i], style="bold cyan")
            live.update(Align.center(text))
            time.sleep(0.04)
        time.sleep(0.5)

    # Flash the banner
    console.print(Align.center(Panel(
        Text(title, style="bold cyan", justify="center"),
        title="[bold green]Polyglot Runtime v2.0[/bold green]",
        subtitle="[italic white]The Universal Compiler[/italic white]",
        border_style="cyan",
        width=60,
        padding=(1, 2)
    )))
    time.sleep(0.5)

def init_project():
    """Run the interactive project initialization wizard."""
    console = Console()
    
    if not HAS_UI_LIBS:
        print("\n[!] 'rich' and 'questionary' libraries are missing.")
        print("    Run 'pip install rich questionary' for the full experience.")
        print("    Falling back to basic input...\n")
        return fallback_init()

    try:
        animate_banner(console)

        console.print(Align.center("[bold white]Welcome to the Qyro Project Wizard[/bold white]\n"))

        # Project Details with styled prompts
        name = questionary.text(
            "Project Name:",
            default=os.path.basename(os.getcwd()),
            style=questionary.Style([('qmark', 'fg:#00ff00 bold'), ('question', 'bold'), ('answer', 'fg:#00ffff')])
        ).ask()

        if name is None: return # Handle Cancel

        desc = questionary.text("Description:").ask()
        if desc is None: return

        # Language Selection
        languages = questionary.checkbox(
            "Select the components/languages you want to use:",
            choices=[
                "Python (Backend API)",
                "Java (High-Performance Logic)",
                "React (Frontend UI)",
                "Go (Systems Programming)",
                "Rust (Safety Critical)"
            ],
            style=questionary.Style([
                 ('qmark', 'fg:#00ff00 bold'),
                 ('question', 'bold'),
                 ('item', 'fg:#ffffff'),
                 ('selected', 'fg:#00ffff bold'),
                 ('pointer', 'fg:#00ff00 bold'),
             ])
        ).ask()

        if languages is None: return

        # Parse selection
        clean_langs = []
        if "Python (Backend API)" in languages: clean_langs.append("python")
        if "Java (High-Performance Logic)" in languages: clean_langs.append("java")
        if "React (Frontend UI)" in languages: clean_langs.append("react")
        if "Go (Systems Programming)" in languages: clean_langs.append("go")
        if "Rust (Safety Critical)" in languages: clean_langs.append("rust")

        # Docker/Kubernetes opt-in (The Feature)
        console.print()
        console.print(Align.center("[bold yellow]Production Readiness[/bold yellow]"))

        enable_docker = questionary.confirm(
            "Enable Docker/Kubernetes support? (Creates .qyro/artifacts)"
        ).ask()

        if enable_docker is None: return

        # Configuration Data
        config = {
            "name": name,
            "description": desc,
            "languages": clean_langs,
            "version": "0.1.0",
            "created_at": time.time(),
            "features": {
                "docker": enable_docker,
                "kubernetes": enable_docker,
                "redlock": False
            }
        }

        # Simulated "Heavy" Work with Animation
        console.print()
        with Progress(
            SpinnerColumn("dots", style="bold cyan"),
            TextColumn("[bold white]{task.description}"),
            BarColumn(bar_width=None, style="cyan", complete_style="green"),
            transient=False,
            console=console
        ) as progress:

            task1 = progress.add_task("Creating Project Structure...", total=100)
            time.sleep(0.5)
            # Create directory
            os.makedirs(".qyro", exist_ok=True)
            progress.update(task1, advance=50)
            time.sleep(0.3)
            progress.update(task1, advance=50)

            task2 = progress.add_task("Generating Configuration...", total=100)
            with open(".qyro/qyro.json", "w") as f:
                json.dump(config, f, indent=4)
            time.sleep(0.4)
            progress.update(task2, advance=100)

            if enable_docker:
                task3 = progress.add_task("Preparing Docker Templates...", total=100)
                os.makedirs(".qyro/artifacts", exist_ok=True)
                time.sleep(0.6)
                progress.update(task3, advance=100)

            task4 = progress.add_task("Scaffolding main.qyro...", total=100)
            if not os.path.exists("main.qyro"):
                generate_main_qyro(clean_langs)
            time.sleep(0.5)
            progress.update(task4, advance=100)

            # Gitignore check
            if os.path.exists(".gitignore"):
                with open(".gitignore", "r") as f:
                    content = f.read()
                if ".qyro/" not in content:
                    with open(".gitignore", "a") as f:
                        f.write("\n.qyro/\n")

        console.print("\n")
        console.print(Panel(
            Align.center(
                f"[bold green]🚀 Project '{name}' Initialized Successfully![/bold green]\n\n"
                f"[white]Languages:[/white] {', '.join(clean_langs)}\n"
                f"[white]Config:[/white] .qyro/qyro.json\n"
                f"[white]Docker:[/white] {'Enabled' if enable_docker else 'Disabled'}\n\n"
                f"[cyan]Run:[/cyan] python run.py main.qyro"
            ),
            border_style="green",
            title="[bold white]Ready to Code[/bold white]",
            subtitle="[italic]Happy Hacking![/italic]",
            width=60
        ))
        
    except KeyboardInterrupt:
        console.print("\n[bold red]Cancelled by user.[/bold red]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        # traceback.print_exc()

def fallback_init():
    """Basic input fallback without UI libs."""
    try:
        name = input("Project Name: ")
        desc = input("Description: ")
        print("\nSelect Languages (comma separated): python, java, react, go")
        langs = input("> ").lower().split(',')
        clean_langs = [l.strip() for l in langs if l.strip()]
        
        config = {
            "name": name,
            "description": desc,
            "languages": clean_langs,
            "version": "0.1.0",
            "features": {"docker": False} 
        }
        
        os.makedirs(".qyro", exist_ok=True)
        with open(".qyro/qyro.json", "w") as f:
            json.dump(config, f, indent=4)

        if not os.path.exists("main.qyro"):
            generate_main_qyro(clean_langs)
            
        print(f"\n[+] Project '{name}' Initialized!")
        
    except KeyboardInterrupt:
        print("\nCancelled.")

def generate_main_qyro(languages: List[str]):
    """Generate a starter main.qyro based on selection."""
    content = ""

    # Always add schema
    content += ">>>schema\n{\n    \"status\": \"healthy\",\n    \"count\": 0\n}\n\n"

    if "python" in languages:
        content += """>>>py:api
import time
from qyro.common.memory import QyroMemory

mem = QyroMemory(create=False)

def run():
    print("[Python] API Service Started")
    while True:
        try:
            state_bytes = mem.read()
            # print(f"[Python] State size: {len(state_bytes)}")
        except:
            pass
        time.sleep(5)

if __name__ == "__main__":
    run()

"""

    if "java" in languages:
        content += """>>>java:worker
import qyro.Qyro;
import qyro.GlobalState;

public class Worker {
    public static void main(String[] args) {
        System.out.println("[Java] Worker Started");
        Qyro qyro = new Qyro();
    }
}

"""

    if "react" in languages:
        content += """>>>react:ui
import { useState, useEffect } from 'react';

const App = () => {
    return <h1>Hello from Qyro React!</h1>;
};
export default App;

"""

    with open("main.qyro", "w") as f:
        f.write(content)

if __name__ == "__main__":
    init_project()
