import os 
import json
from tkinter import filedialog
import subprocess
import time
import cv2
import pyautogui
import numpy as np
import pyperclip
from utilities.actions import *
from utilities.capture import * 
from utilities.detection import *
from truecloud import start_app_and_login,TEMPLATES_DIR,upscale,MATCHING_THRESHOLD,click,center_cordinates,SCRIPT_DIR
ITEMS = ["NAIPURA,01-PANWARI"]

# Runtime-tunable values controlled by settings in __main__.
PLAY_BUTTON_THRESHOLD = 0.6
PIXEL_MOVEMENT = 25


def _movement_steps():
    major = max(1, int(PIXEL_MOVEMENT))
    minor = max(1, major // 3)
    return major, minor

def search():
    try:
        for trying in range(1, 4):
            started = start_app_and_login()
            if started:
                print("app started")
                break
            raise FileExistsError("Failed to start app retrying..")

        search_tpl = os.path.join(TEMPLATES_DIR, "search.png")
        resized_image = upscale(search_tpl)
        screenshot_view = pyautogui.screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot_view), cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(screenshot_cv, resized_image, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= MATCHING_THRESHOLD:
            x, y = max_loc
            h, w = resized_image.shape[:2]
            click_open_camera()   

            click(x, y, h, w)
            time.sleep(0.15)
            write_to_search(ITEMS[0], x, y, h, w)
            clickbelow(x, y, h, w)
            got_images=clickabove(x, y, h, w,first=True)
            time.sleep(1.5)
    except Exception:
        pass

def clickabove(x, y, h, w,first=False):

    time.sleep(0.5)

    screen_w, screen_h = pyautogui.size()

    roi_x = 0
    roi_w = int(screen_w * 0.21)

    roi_y = max(0, y - 450)
    roi_h = 450

    print(f"[DEBUG] ROI: x={roi_x}, y={roi_y}, w={roi_w}, h={roi_h}")

    hsv_img, offset = capture_list_area(
        roi_x=roi_x,
        roi_y=roi_y,
        roi_w=roi_w,
        roi_h=roi_h
    )

    if hsv_img is None:
        print("[WARNING] Failed to capture list area")
        return False

    highlight = find_blue_highlight(hsv_img, offset=offset)

    if highlight is None:
        print("[WARNING] No blue highlight found")
        return False

    abs_x, abs_y, card_w, card_h = highlight
    cx = abs_x + card_w // 2
    cy = abs_y + card_h // 2

    time.sleep(1)

    print(f"[INFO] Clicking highlight at ({cx}, {cy})")
    dx =abs(cx - x)
    dy = abs(cy - y)
    
    print(f"[DEBUG] dx={dx}, dy={dy}")


    if abs(dx)<= 50:
        offset_x, offset_y = 80, +8
        print("[INFO] Using alternate offset")
    else:
        offset_x, offset_y = 95, -17
        print("[INFO] Using default offset")

    pyautogui.click(cx+80,cy-8)

    while True:
        major_step, minor_step = _movement_steps()
        px, py = capture_view_play(
            cx + offset_x,
            cy + offset_y,
            threshold=PLAY_BUTTON_THRESHOLD
        )

        if px is None or py is None:
            print("[INFO] No more play buttons found, exiting loop")
            print("[INFO] Scrolling down 50px")
            pyautogui.scroll(-major_step)
            time.sleep(0.7)
            if_end=check_end()
            if if_end:
                get_to_final_step(cx, cy, offset_x, offset_y)
                break
            continue
        
        play_cx = px
        play_cy = py 
        
        print(f"[INFO] Found play button at ({play_cx}, {play_cy}), clicking...")
        click_twice(play_cx,play_cy)
        time.sleep(3)
        
        click_open_camera(initial=False)
        time.sleep(1.5)
        
        print(f"[INFO] Re-clicking play button at ({play_cx}, {play_cy})")

        click_twice(play_cx,play_cy)
        
        time.sleep(1.5)

        print("[INFO] Scrolling down 50px")
        pyautogui.scroll(-major_step)
        time.sleep(0.6)  
        pyautogui.scroll(-minor_step)
        time.sleep(0.4)
    return True

def get_to_final_step(cx, cy, offset_x, offset_y, max_steps=13):
    major_step, minor_step = _movement_steps()
    pyautogui.scroll(-major_step)
    probe_x = cx + offset_x
    probe_y = cy + offset_y

    pyautogui.moveTo(probe_x, probe_y, duration=0.1)
    time.sleep(0.2)

    for i in range(max_steps):
        
        px, py = capture_view_play(
            probe_x,
            probe_y,
            threshold=PLAY_BUTTON_THRESHOLD
        )

        if px is None or py is None:
            print(f"[INFO] step {i+1}: no play at probe ({probe_x},{probe_y}), moving probe down")
            probe_y += major_step
            pyautogui.moveTo(probe_x, probe_y, duration=0.08)
            time.sleep(0.25)
            probe_y += minor_step
            pyautogui.moveTo(probe_x, probe_y, duration=0.08)
            time.sleep(0.35)
            continue

        play_cx, play_cy = px, py

        print(f"[INFO] step {i+1}: found play at ({play_cx}, {play_cy}), clicking...")
        click_twice(play_cx, play_cy)
        time.sleep(3)

        click_open_camera(initial=False)
        time.sleep(1.5)

        print(f"[INFO] step {i+1}: re-clicking play at ({play_cx}, {play_cy})")
        click_twice(play_cx, play_cy)
        time.sleep(1.5)

        probe_y += major_step
        pyautogui.moveTo(probe_x, probe_y, duration=0.08)
        time.sleep(0.25)
        probe_y += minor_step
        pyautogui.moveTo(probe_x, probe_y, duration=0.08)
        time.sleep(0.35)

    check_images_view()
    return True

if __name__ == "__main__":
    from rich.console import Console, Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt
    from rich.live import Live
    from rich.spinner import Spinner
    from rich.text import Text
    from rich import box

    console = Console()

    SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")

    DEFAULT_SETTINGS = {
        "threshold": PLAY_BUTTON_THRESHOLD,
        "pixel_movement": PIXEL_MOVEMENT,
        "generate_report": True,
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

    settings = load_settings()

    # Apply settings to the runtime values used by play detection/movement only.
    PLAY_BUTTON_THRESHOLD = float(settings["threshold"])
    PIXEL_MOVEMENT = int(settings["pixel_movement"])

    def show_header():
        console.clear()
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
        subtitle = Text("AUTOMATION CONSOLE -- Developed By BrainPan Innovations..", style="#9aa7b8")
        divider = Text("─" * 86, style="#3f566e")

        console.print(
            Panel(
                Group(logo, divider, subtitle),
                subtitle="OpenCode-style Runner",
                border_style="#4aa8d8",
                box=box.HEAVY,
                padding=(1, 2),
            )
        )

    def show_settings():
        global PLAY_BUTTON_THRESHOLD, PIXEL_MOVEMENT

        while True:
            show_header()

            table = Table(title="Current Settings", show_header=True)
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Play Detection Threshold", str(settings["threshold"]))
            table.add_row("Pixel Movement", f"{settings['pixel_movement']} px")
            table.add_row(
                "Generate Report",
                "TRUE" if settings["generate_report"] else "FALSE",
            )

            console.print(table)
            console.print()

            console.print("[1] Change play detection threshold")
            console.print("[2] Change pixel movement")
            console.print("[3] Toggle report generation")
            console.print("[4] Back")

            choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4"])

            if choice == "1":
                value = Prompt.ask(
                    "Enter play detection threshold",
                    default=str(settings["threshold"]),
                )

                try:
                    value = float(value)
                    if 0 < value <= 1:
                        settings["threshold"] = value
                        PLAY_BUTTON_THRESHOLD = value
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
                    "Enter pixel movement",
                    default=str(settings["pixel_movement"]),
                )

                try:
                    value = int(value)
                    if value <= 0:
                        console.print("[red]Pixel movement must be greater than 0[/red]")
                        time.sleep(1)
                        continue

                    settings["pixel_movement"] = value
                    PIXEL_MOVEMENT = value
                    save_settings(settings)

                    console.print(f"\n[green]Pixel movement updated to {value}px[/green]")
                    time.sleep(1)
                except ValueError:
                    console.print("[red]Invalid number[/red]")
                    time.sleep(1)

            elif choice == "3":
                settings["generate_report"] = not settings["generate_report"]
                save_settings(settings)

                state = "enabled" if settings["generate_report"] else "disabled"
                console.print(f"\n[green]Report generation {state}[/green]")
                time.sleep(1)

            elif choice == "4":
                break

    def run_automation():
        show_header()

        console.print(
            Panel(
                (
                    f"\n[cyan]Play Threshold:[/cyan] {settings['threshold']}"
                    f"\n[cyan]Pixel Movement:[/cyan] {settings['pixel_movement']} px"
                    f"\n[cyan]Generate Report:[/cyan] "
                    f"{'TRUE' if settings['generate_report'] else 'FALSE'}\n"
                ),
                title="Run Configuration",
                border_style="#3b82f6",
                box=box.ROUNDED,
            )
        )

        console.print()
        console.print("[bold cyan]Starting new run...[/bold cyan]\n")

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

        with Live(
            Spinner("dots", text=Text(" Observing automation...", style="cyan")),
            console=console,
            refresh_per_second=10,
        ):
            while thread.is_alive():
                time.sleep(0.1)

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

        if settings["generate_report"]:
            console.print("\n[cyan]Report generation enabled.[/cyan]")

        Prompt.ask("\nPress Enter to return to menu", default="")

    def main_menu():
        while True:
            show_header()
            console.print(
                Panel(
                    (
                        "[bold #70d7ff][1][/bold #70d7ff] New Run\n"
                        "[bold #70d7ff][2][/bold #70d7ff] Settings\n"
                        "[bold #70d7ff][3][/bold #70d7ff] Exit"
                    ),
                    title="Main Menu",
                    subtitle="Choose an action",
                    border_style="#4aa8d8",
                    box=box.HEAVY,
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
                break

    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Automation interrupted by user.[/yellow]")
    except Exception as e:
        console.print(
            Panel(
                f"[red]Unexpected error[/red]\n\n{e}",
                border_style="red",
            )
        )
    finally:
        console.print("\n[dim]Press Enter to exit...[/dim]")
        input()