import os
import time
import cv2
import numpy as np
import pyautogui

from truecloud import TEMPLATES_DIR, upscale
import utilities.report_manager as report_manager

CARD_HEIGHT = 52
REPORT_GENERATION=True

def _Set_Report_Generation(status):
    global REPORT_GENERATION
    try:
        REPORT_GENERATION=status
    except (TypeError, ValueError):
        REPORT_GENERATION=False
    
    

def capture_list_area(roi_x=None, roi_y=None, roi_w=None, roi_h=None):
    print(f"[DEBUG] Capturing list area...")

    try:
        screenshot = pyautogui.screenshot(region=(roi_x, roi_y, roi_w, roi_h))
        bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        print(f"[DEBUG] Captured shape: {hsv.shape}")

        return hsv, (roi_x, roi_y)

    except Exception as e:
        print(f"[ERROR] Capture failed: {e}")
        return None, None


def capture_view_play(x, y, size=100, threshold=0.6, template_name="click_play.png", first=False):
    size = int(size)
    screen_w, screen_h = pyautogui.size()
    shift = -10
    top_trim = max(4, size // 12)
    bottom_trim = max(12, size // 4)

    left = 0
    top = max(0, y - size // 2 + shift + top_trim)

    right = min(screen_w, x + size // 2)

    width = right - left
    height = CARD_HEIGHT
    w = width
    h = min(height, screen_h - top)
    screenshot = pyautogui.screenshot(region=(left, top, w, h))
    crop_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    crop_gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)

    tpl_path = os.path.join(TEMPLATES_DIR, template_name)
    tpl = upscale(tpl_path)
    if tpl is None:
        return None, None
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
        return abs_cx, abs_cy

    if max_val >= threshold:
        time.sleep(0.5)
        tx, ty = max_loc
        th, tw = tpl_gray.shape[:2]
        abs_cx = left + tx + tw // 2
        abs_cy = top + ty + th // 2
        return abs_cx, abs_cy

    return None, None
