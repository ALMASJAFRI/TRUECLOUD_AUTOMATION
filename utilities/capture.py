import os
import time
import cv2
import numpy as np
import pyautogui

from truecloud import TEMPLATES_DIR, upscale
import utilities.report_manager as report_manager

CARD_HEIGHT = 52
REPORT_GENERATION = True
VERBOSE_LOGS = False

# Set this to your actual spinner/loading-icon template filename.
# Put a cropped screenshot of the spinning "⟳" icon in TEMPLATES_DIR.
SPINNER_TEMPLATE = "spinner.png"


def log(message):
    if VERBOSE_LOGS:
        print(message)


def Set_Report_Generation(status):
    global REPORT_GENERATION
    try:
        REPORT_GENERATION = status
    except (TypeError, ValueError):
        REPORT_GENERATION = False


def capture_list_area(roi_x=None, roi_y=None, roi_w=None, roi_h=None):
    log(f"[DEBUG] Capturing list area...")

    try:
        screenshot = pyautogui.screenshot(region=(roi_x, roi_y, roi_w, roi_h))
        bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        log(f"[DEBUG] Captured shape: {hsv.shape}")

        return hsv, (roi_x, roi_y)

    except Exception as e:
        log(f"[ERROR] Capture failed: {e}")
        return None, None


def advance_one_card(wait_after_press=0.35):
    """
    Move selection to the next card using the Down key.
    One keypress = exactly one card — no pixel/scroll guessing.
    Caller is responsible for ensuring the list has keyboard focus
    (e.g. click the current row once before calling this if needed).
    """
    pyautogui.press('down')
    time.sleep(wait_after_press)
    wait_for_row_loaded()


def wait_for_row_loaded(timeout=2.0, poll=0.15):
    """
    Block until the loading-spinner template is no longer visible
    on screen, so we don't capture a half-rendered row/ID.
    If the template file is missing, falls back to a fixed short wait.
    """
    tpl_path = os.path.join(TEMPLATES_DIR, SPINNER_TEMPLATE)
    spinner_tpl = upscale(tpl_path)

    if spinner_tpl is None:
        log("[WARNING] Spinner template not found, using fixed fallback wait")
        time.sleep(0.5)
        return False

    spinner_gray = spinner_tpl if len(spinner_tpl.shape) == 2 else cv2.cvtColor(spinner_tpl, cv2.COLOR_BGR2GRAY)

    t0 = time.time()
    while time.time() - t0 < timeout:
        screenshot = pyautogui.screenshot()
        gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(gray, spinner_gray, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)

        if max_val < 0.6:
            return True

        time.sleep(poll)

    log("[WARNING] Row still loading after timeout, capturing anyway")
    return False


def capture_view_play(x, y, size=100, threshold=0.6, template_name="click_play.png", first=False):
    size = int(size)
    screen_w, screen_h = pyautogui.size()

    # width: restored full-width calc using offset-adjusted x, unchanged math
    left = 0
    right = min(screen_w, x + size // 2)
    w = right - left

    # height: y is the card's BOTTOM edge, window ends exactly there
    top = max(0, int(y) - CARD_HEIGHT)
    h = min(CARD_HEIGHT, screen_h - top)
    
    screenshot = pyautogui.screenshot(region=(left, top, w, h))
    crop_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    crop_gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)

    tpl_path = os.path.join(TEMPLATES_DIR, template_name)
    tpl = upscale(tpl_path)
    if tpl is None:
        return None, None, crop_bgr
    tpl_gray = tpl if len(tpl.shape) == 2 else cv2.cvtColor(tpl, cv2.COLOR_BGR2GRAY)

    res = cv2.matchTemplate(crop_gray, tpl_gray, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(res)

    if REPORT_GENERATION:
        report_manager.save_card_screenshot(crop_bgr)

    if first:
        tx, ty = max_loc
        th, tw = tpl_gray.shape[:2]
        abs_cx = left + tx + tw // 2
        abs_cy = top + ty + th // 2
        return abs_cx, abs_cy, crop_bgr

    if max_val >= threshold:
        tx, ty = max_loc
        th, tw = tpl_gray.shape[:2]
        abs_cx = left + tx + tw // 2
        abs_cy = top + ty + th // 2
        return abs_cx, abs_cy, crop_bgr

    return None, None, crop_bgr