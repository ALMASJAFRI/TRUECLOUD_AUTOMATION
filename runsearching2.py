import os 
import json
from tkinter import filedialog
import subprocess
import time
import cv2
import pyautogui
import numpy as np
import pyperclip
from utilities.report_manager import *
from utilities.actions import *
from utilities.capture import * 
from utilities.detection import *
from utilities.console import load_settings, main_menu,PLAY_BUTTON_THRESHOLD,PIXEL_MOVEMENT
from truecloud import start_app_and_login,TEMPLATES_DIR,upscale,MATCHING_THRESHOLD,click,center_cordinates,SCRIPT_DIR
ITEMS = ["NAIPURA,01-PANWARI"]

VERBOSE_LOGS = False
settings = load_settings()


def log(message):
    if VERBOSE_LOGS:
        print(message)


def _movement_steps():
    major = max(1, int(PIXEL_MOVEMENT))
    minor = max(1, major // 3)
    return major, minor

def search():
    try:
        for trying in range(1, 4):
            started = start_app_and_login()
            if started:
                log("app started")
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

    log(f"[DEBUG] ROI: x={roi_x}, y={roi_y}, w={roi_w}, h={roi_h}")

    hsv_img, offset = capture_list_area(
        roi_x=roi_x,
        roi_y=roi_y,
        roi_w=roi_w,
        roi_h=roi_h
    )

    if hsv_img is None:
        log("[WARNING] Failed to capture list area")
        return False

    highlight = find_blue_highlight(hsv_img, offset=offset)

    if highlight is None:
        log("[WARNING] No blue highlight found")
        return False

    abs_x, abs_y, card_w, card_h = highlight
    cx = abs_x + card_w // 2
    cy = abs_y + card_h // 2

    time.sleep(1)

    log(f"[INFO] Clicking highlight at ({cx}, {cy})")
    dx =abs(cx - x)
    dy = abs(cy - y)
    
    log(f"[DEBUG] dx={dx}, dy={dy}")


    if abs(dx)<= 50:
        offset_x, offset_y = 80, +8
        log("[INFO] Using alternate offset")
    else:
        offset_x, offset_y = 95, -17
        log("[INFO] Using default offset")

    pyautogui.click(cx+80,cy-8)

    while True:
        major_step, minor_step = _movement_steps()
        px, py = capture_view_play(
            cx + offset_x,
            cy + offset_y,
            threshold=PLAY_BUTTON_THRESHOLD
        )

        if px is None or py is None:
            log("[INFO] No more play buttons found, exiting loop")
            log("[INFO] Scrolling down 50px")
            if settings["generate_report"]:
                end_cycle(False,False)

            pyautogui.scroll(-major_step)
            time.sleep(0.7)
            if_end=check_end()
            if if_end:
                get_to_final_step(cx, cy, offset_x, offset_y)
                break
            continue
        
        play_cx = px
        play_cy = py 
        
        log(f"[INFO] Found play button at ({play_cx}, {play_cy}), clicking...")
        click_twice(play_cx,play_cy)
        time.sleep(3)
        
        click_open_camera(initial=False)
        time.sleep(1.5)
        
        log(f"[INFO] Re-clicking play button at ({play_cx}, {play_cy})")

        click_twice(play_cx,play_cy)
        
        time.sleep(1.5)

        log("[INFO] Scrolling down 50px")
        pyautogui.scroll(-major_step)
        time.sleep(0.6)  
        if settings["generate_report"]:
            end_cycle(True,True)
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
            log(f"[INFO] step {i+1}: no play at probe ({probe_x},{probe_y}), moving probe down")
            if settings["generate_report"]:
                end_cycle(False,False)
            probe_y += major_step
            pyautogui.moveTo(probe_x, probe_y, duration=0.08)
            time.sleep(0.25)
            probe_y += minor_step
            pyautogui.moveTo(probe_x, probe_y, duration=0.08)
            time.sleep(0.35)
            continue

        play_cx, play_cy = px, py

        log(f"[INFO] step {i+1}: found play at ({play_cx}, {play_cy}), clicking...")
        click_twice(play_cx, play_cy)
        time.sleep(3)

        click_open_camera(initial=False)
        time.sleep(1.5)

        log(f"[INFO] step {i+1}: re-clicking play at ({play_cx}, {play_cy})")
        click_twice(play_cx, play_cy)
        time.sleep(1.5)

        probe_y += major_step
        pyautogui.moveTo(probe_x, probe_y, duration=0.08)
        time.sleep(0.25)
        if settings["generate_report"]:
            end_cycle(True,True)
        probe_y += minor_step
        pyautogui.moveTo(probe_x, probe_y, duration=0.08)
        time.sleep(0.35)

    check_images_view()
    return True

if __name__ == "__main__":
    from rich.console import Console, Group
    from rich.panel import Panel
    console=Console()
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