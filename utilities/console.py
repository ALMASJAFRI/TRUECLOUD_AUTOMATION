import json
import os
import time
import subprocess
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text
from rich import box
from truecloud import SCRIPT_DIR
from utilities.capture import Set_Report_Generation, set_play_button_threshold
from utilities.detection import set_check_images_view_delay
from utilities.report_manager import save_report, stop_event
from truecloud import set_After_Login_Delay
import sys
console = Console()

PLAY_BUTTON_THRESHOLD = 0.6

SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")


def clear_terminal():
    subprocess.run(
        "cls" if os.name == "nt" else "clear",
        shell=True,
        check=False,
    )
def full_panel(content, title=None, subtitle=None, border_style="#4aa8d8", box_style=box.HEAVY, padding=(1, 2)):
    width = max(70, console.width - 4)
    return Panel(
        content,
        title=title,
        subtitle=subtitle,
        border_style=border_style,
        box=box_style,
        padding=padding,
        width=width,
        expand=True,
    )

DEFAULT_SETTINGS = {
    "Play Button Threshold": PLAY_BUTTON_THRESHOLD,
    "After Login Delay" : 0.2,
    "Camera Close Delay": 0.5,
    "Generate Report": True,
    "Mapper File Path": "",
}

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return DEFAULT_SETTINGS.copy()

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            settings = json.load(f)

        return {
            **DEFAULT_SETTINGS,
            **settings,
        }
    except Exception:
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

def resolve_mapper_file():
    from tkinter import filedialog

    path = settings.get("Mapper File Path", "")

    if path and os.path.exists(path):
        return path

    console.print("[yellow]Goashray mapper Excel file not found.[/yellow]")
    console.print("[yellow]Please select the Goashray List Excel file.[/yellow]")

    path = filedialog.askopenfilename(
        title="SELECT GOASHRAY EXCEL",
        filetypes=[("Excel files", "*.xlsx"), ("ALL files", "*.*")]
    )

    if not path or not os.path.exists(path):
        raise FileNotFoundError("Goashray mapper Excel file is required")

    settings["Mapper File Path"] = path
    save_settings(settings)
    return path

settings = load_settings()

# Apply settings to the runtime values used by play detection/movement only.
set_play_button_threshold(float(settings["Play Button Threshold"]))
set_check_images_view_delay(settings.get("Camera Close Delay", 0.5))

def show_header():
    clear_terminal()
    logo = Text(
        "\n".join(
            [
                "████████╗██████╗ ██╗   ██╗███████╗ ██████╗██╗      ██████╗ ██╗   ██╗██████╗ ",
                "╚══██╔══╝██╔══██╗██║   ██║██╔════╝██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗",
                "   ██║   ██████╔╝██║   ██║█████╗  ██║     ██║     ██║   ██║██║   ██║██║  ██║",
                "   ██║   ██╔══██╗██║   ██║██╔══╝  ██║     ██║     ██║   ██║██║   ██║██║  ██║",
                "   ██║   ██║  ██║╚██████╔╝███████╗╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝",
                "   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚══════╝ ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ ",
            ]
        ),
        style="bold #69d2ff",
    )
    subtitle = Text("AUTOMATION CONSOLE -- Reducing Manual Efforts..", style="#9aa7b8")
    divider = Text("─" * 86, style="#3f566e")

    console.print(
        full_panel(
            Group(logo, divider, subtitle),
            subtitle="CLI Tool",
            border_style="#4aa8d8",
            box_style=box.HEAVY,
            padding=(1, 2),
        )
    )

def show_settings():
    while True:
        show_header()

        table = Table(title="Current Settings", show_header=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Play Detection Threshold", str(settings["Play Button Threshold"]))
        table.add_row("After Login Delay", str(settings["After Login Delay"]))
        table.add_row("Camera Close Delay", f"{settings['Camera Close Delay']} s")
        table.add_row(
            "Mapper Excel Path",
            settings.get("Mapper File Path", "") or "(not set)",
        )
        table.add_row(
            "Generate Report",
            "TRUE" if settings["Generate Report"] else "FALSE",
        )

        console.print(table)
        console.print()

        console.print("[1] Change Play Button Threshold")
        console.print("[2] Change After Login Delay")
        console.print("[3] Change Camera Close Delay")
        console.print("[4] Set Goashray mapper Excel path")
        console.print("[5] Toggle Generate Report")
        console.print("[6] Back")

        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4", "5","6"])

        if choice == "1":
            value = Prompt.ask(
                "Enter play detection threshold",
                default=str(settings["Play Button Threshold"]),
            )

            try:
                value = float(value)
                if 0 < value <= 1:
                    settings["Play Button Threshold"] = value
                    set_play_button_threshold(value)
                    save_settings(settings)
                    console.print(f"\n[green]Threshold updated to {value}[/green]")
                    time.sleep(1)
                else:
                    console.print("[red]Threshold must be between 0 and 1[/red]")
                    time.sleep(1)
            except ValueError:
                console.print("[red]Invalid number[/red]")
                time.sleep(1)

        elif choice == "2":
            value = Prompt.ask(
                "Enter After Login Delay (seconds)",
                default=str(settings["After Login Delay"]),
            )
            try:
                value = float(value)
                if value < 0:
                    console.print("[red]Delay cannot be negative[/red]")
                    time.sleep(1)
                    continue

                settings["After Login Delay"] = value
                set_After_Login_Delay(value)
                save_settings(settings)

                console.print(f"\n[green]After login delay updated to {value}s[/green]")
                time.sleep(1)
            except ValueError:
                console.print("[red]Invalid number[/red]")
                time.sleep(1)
        elif choice == "3":
            value = Prompt.ask(
                "Enter Camera Close Delay (seconds)",
                default=str(settings["Camera Close Delay"]),
            )

            try:
                value = float(value)
                if value < 0:
                    console.print("[red]Delay cannot be negative[/red]")
                    time.sleep(1)
                    continue

                settings["Camera Close Delay"] = value
                set_check_images_view_delay(value)
                save_settings(settings)

                console.print(f"\n[green]Close view delay updated to {value}s[/green]")
                time.sleep(1)
            except ValueError:
                console.print("[red]Invalid number[/red]")
                time.sleep(1)

        elif choice == "4":
            console.print("[yellow]Select the Goashray mapper Excel file.[/yellow]")
            try:
                path = resolve_mapper_file()
                console.print(f"\n[green]Mapper Excel path set to:[/green] {path}")
            except FileNotFoundError as e:
                console.print(f"[red]{e}[/red]")
            time.sleep(1)

        elif choice == "5":
            settings["Generate Report"] = not settings["Generate Report"]
            save_settings(settings)
            Set_Report_Generation(settings["Generate Report"])
            state = "enabled" if settings["Generate Report"] else "disabled"
            console.print(f"\n[green]Report generation {state}[/green]")
            time.sleep(1)

        elif choice == "6":
            return

def run_automation():
    show_header()

    console.print(
        full_panel(
            (
                f"\n[cyan]Play Threshold:[/cyan] {settings['Play Button Threshold']}"
                f"\n[cyan]After Login Delay:[/cyan] {settings['After Login Delay']}"
                f"\n[cyan]Camera Close Delay:[/cyan] {settings['Camera Close Delay']} s"
                f"\n[cyan]Generate Report:[/cyan] "
                f"{'TRUE' if settings['Generate Report'] else 'FALSE'}\n"
            ),
            title="Run Configuration",
            border_style="#3b82f6",
            box_style=box.ROUNDED,
            padding=(1, 2),
        )
    )

    console.print()
    console.print("[bold cyan]Starting new run...[/bold cyan]\n")

    from utilities.OCR_Worker import _set_mapper_file_path, start_worker

    mapper_path = resolve_mapper_file()
    _set_mapper_file_path(mapper_path)
    start_worker()

    from runsearching2 import search

    result = {"finished": False, "error": None}

    def worker():
        try:
            search()
            result["finished"] = True
        except Exception as e:
            result["error"] = e

    import threading

    thread = threading.Thread(target=worker)
    thread.start()

    try:
        with Live(
            Spinner("dots", text=Text(" Observing automation...", style="cyan")),
            console=console,
            refresh_per_second=10,
        ):
            while thread.is_alive():
                time.sleep(0.1)
    except KeyboardInterrupt:
         with Live(
                    Spinner("dots", text=Text("Generating Report ..", style="cyan")),
                    console=console,
                    refresh_per_second=10,
                ):
                    stop_event.set()
                    thread.join(timeout=10)
                    if settings["Generate Report"]:
                        console.print("\n[yellow]Saving partial report...[/yellow]")
                        save_report(timeout=10)
                    console.print("[yellow]Automation stopped. Partial report saved.[/yellow]")
                    return
         
    if result["error"]:
        console.print()
        console.print(
            Panel(
                f"[red]Automation failed[/red]\n\n{result['error']}",
                border_style="red",
            )
        )
    else:
        console.print()
        console.print(
            Panel(
                "[bold green]RUN COMPLETED SUCCESSFULLY[/bold green]",
                border_style="green",
            )
        )

    if settings["Generate Report"]:
        console.print("\n[yellow]Report is generating, please wait...[/yellow]")
        try:
            save_report()
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted during report generation, saving partial report...[/yellow]")
            save_report(timeout=10)

    Prompt.ask("\nPress Enter to return to menu", default="")

def main_menu():
    while True:
        show_header()
        console.print(
            full_panel(
                (
                    "[bold #70d7ff][1][/bold #70d7ff] New Run\n"
                    "[bold #70d7ff][2][/bold #70d7ff] Settings\n"
                    "[bold #70d7ff][3][/bold #70d7ff] Exit"
                ),
                title="Main Menu",
                subtitle="Choose an action",
                border_style="#4aa8d8",
                box_style=box.HEAVY,
                padding=(1, 2),
            )
        )

        choice = Prompt.ask("\nSelect option", choices=["1", "2", "3"])

        if choice == "1":
            run_automation()
        elif choice == "2":
            show_settings()
        elif choice == "3":
            console.print("\n[cyan]Goodbye.[/cyan]")
            time.sleep(3)
            clear_terminal()
            sys.exit(0)
            return