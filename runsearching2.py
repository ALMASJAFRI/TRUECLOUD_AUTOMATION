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
import utilities.capture as capture
from utilities.detection import * 
from utilities.console import main_menu
from truecloud import start_app_and_login, TEMPLATES_DIR, upscale, MATCHING_THRESHOLD, click, center_cordinates, SCRIPT_DIR

ITEMS = ["NAIPURA,01-PANWARI"]

VERBOSE_LOGS = False


def log(message):
    if VERBOSE_LOGS:
        print(message)


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
            got_images = clickabove(x, y, h, w, first=True)
            time.sleep(1.5)
    except Exception:
        pass


def detect_current_highlight(y):
    
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
        return None

    highlight = find_blue_highlight(hsv_img, offset=offset)
    if highlight is None:
        return None

    abs_x, abs_y, card_w, card_h = highlight
    cx = abs_x + card_w // 2
    cy = abs_y + card_h // 2
    card_bottom_y = abs_y + card_h

    return cx, cy, card_bottom_y, card_w


SCREENSHOT_DIFF_THRESHOLD = 0.2


def _reached_end(prev_img, current_img):
    """
    End-of-list detection. Returns True when the current card screenshot is
    essentially identical to the previous one (i.e. pressing Down changed
    nothing), meaning every camera card has been scanned.
    """
    if prev_img is None or current_img is None:
        return False

    if prev_img.shape != current_img.shape:
        return False

    mean_diff = float(np.mean(cv2.absdiff(prev_img, current_img)))
    log(f"[INFO] Card screenshot diff: {mean_diff:.2f}")

    return mean_diff < SCREENSHOT_DIFF_THRESHOLD


def clickabove(x, y, h, w, first=False):

    time.sleep(0.5)

    # Initial detection — establish offset_x based on first highlight position
    detected = detect_current_highlight(y)
    if detected is None:
        log("[WARNING] No blue highlight found at start")
        return False

    cx, cy, card_bottom_y, card_w = detected

    log(f"[INFO] Initial highlight at ({cx}, {cy})")
    dx = abs(cx - x)

    if abs(dx) <= 50:
        offset_x = 80
        log("[INFO] Using alternate offset")
    else:
        offset_x = 95
        log("[INFO] Using default offset")

    pyautogui.click(cx + 80, cy - 8)
    time.sleep(1)

    prev_img = None

    while True:
        if stop_event.is_set():
            return False

        # Capture using current highlight position (no stored cy, always fresh)
        px, py, current_img = capture_view_play(
            cx + offset_x,
            card_bottom_y,
        )

        if _reached_end(prev_img, current_img):
            log("[INFO] Screenshot unchanged after movement, end of list reached")
            if check_end():
                check_images_view()
            break

        prev_img = current_img

        if px is None or py is None:
            log("[INFO] No more play buttons found, exiting loop")
            log("[INFO] Advancing to next card")
            if capture.REPORT_GENERATION:
                end_cycle(False, False)

            advance_one_card()

            detected = detect_current_highlight(y)
            if detected is None:
                break
            cx, cy, card_bottom_y, card_w = detected
            continue
        play_cx = px
        play_cy = py

        log(f"[INFO] Found play button at ({play_cx}, {play_cy}), clicking...")
        click_twice(play_cx, play_cy)
        time.sleep(3)

        click_open_camera(initial=False)
        time.sleep(1.5)

        log(f"[INFO] Re-clicking play button at ({play_cx}, {play_cy})")
        click_twice(play_cx, play_cy)

        time.sleep(0.7)

        log("[INFO] Advancing to next card")
        advance_one_card()

        # Re-detect highlight at new position
        detected = detect_current_highlight(y)
        if detected is not None:
            cx, cy, card_bottom_y, card_w = detected
        else:
            log("[WARNING] Lost highlight after advancing, keeping last known position")

        if capture.REPORT_GENERATION:
            end_cycle(True, True)
    return True

if __name__ == "__main__":
    from rich.console import Console, Group
    from rich.panel import Panel
    console = Console()
    try:
        main_menu()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Automation interrupted by user.[/yellow]")
        main_menu()
    except Exception as e:
        console.print(
            Panel(
                f"[red]Unexpected error[/red]\n\n{e}",
                border_style="red",
            )
        )
        input("\nPress Enter to close...")