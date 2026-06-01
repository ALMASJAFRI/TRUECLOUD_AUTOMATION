
import os
import json
from tkinter import filedialog
import subprocess
import time
import cv2
import pyautogui
import numpy as np
import pyperclip

from truecloud import start_app_and_login, TEMPLATES_DIR, upscale, MATCHING_THRESHOLD, click, center_cordinates, SCRIPT_DIR
from logger_setup import get_logger, get_screenshot_path

logger = get_logger(__name__)

ITEMS = ["NAIPURA,01-PANWARI"]


def search():
    try:
        for trying in range(1, 4):
            started = start_app_and_login()
            if started:
                logger.info("app started")
                break
            if trying == 3:
                raise FileExistsError("Failed to start app retrying..")
            time.sleep(1)

        search_tpl = os.path.join(TEMPLATES_DIR, "search.png")
        resized_image = upscale(search_tpl)
        screenshot_view = pyautogui.screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot_view), cv2.COLOR_RGB2GRAY)

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
            clickabove(x, y, h, w, first=True)
            time.sleep(1.5)
    except Exception:
        logger.exception("Exception in search()")


def clickbelow(x, y, h, w):
    center = center_cordinates(x, y, h, w)
    pyautogui.click(center[0], center[1] + 20)


def clickabove(x, y, h, w, first=False):
    logger.info("========== ENTER clickabove() ==========")
    time.sleep(0.5)

    screen_w, screen_h = pyautogui.size()
    logger.debug(f"[DEBUG] Screen size: {screen_w}x{screen_h}")

    roi_x = 0
    roi_w = int(screen_w * 0.21)

    roi_y = max(0, y - 450)
    roi_h = 450

    logger.debug(f"[DEBUG] ROI -> x:{roi_x}, y:{roi_y}, w:{roi_w}, h:{roi_h}")

    hsv_img, offset = capture_list_area(
        roi_x=roi_x,
        roi_y=roi_y,
        roi_w=roi_w,
        roi_h=roi_h
    )

    logger.debug(f"[DEBUG] Offset received: {offset}")

    if hsv_img is None:
        logger.error("[ERROR] hsv_img is None")
        return False

    highlight = find_blue_highlight(hsv_img, offset=offset)

    if highlight is None:
        logger.error("[ERROR] No highlight found")
        return False

    abs_x, abs_y, card_w, card_h = highlight
    cx = abs_x + card_w // 2
    cy = abs_y + card_h // 2

    logger.debug(f"[DEBUG] Highlight center -> ({cx}, {cy})")

    #pyautogui.click(cx + 80, cy - 8)
    pyautogui.click(204,131)
    logger.debug("[DEBUG] Clicked highlight")
    step = 0

    while True:
        step += 1
        logger.info(f"----- LOOP STEP {step} -----")

        px, py = capture_view_play(204,122)

        logger.debug(f"[DEBUG] capture_view_play -> px:{px}, py:{py}")

        if px is None or py is None:
            logger.info("[INFO] No play detected, scrolling...")
            pyautogui.scroll(-25)
            time.sleep(0.4)

            if check_end():
                logger.info("[INFO] End detected -> moving to final step")
                get_to_final_step(cx, cy, 80, -17)
                break
            continue

        logger.info(f"[ACTION] Clicking ({px},{py})")
        click_twice(px, py)
        time.sleep(3)

        logger.info("[ACTION] Opening camera")
        click_open_camera(initial=False)
        time.sleep(1.5)

        logger.info("[ACTION] Re-clicking")
        click_twice(px, py)
        time.sleep(1.2)

        logger.info("[ACTION] Scrolling")
        pyautogui.scroll(-40)
        time.sleep(0.3)
        pyautogui.scroll(-17)
        time.sleep(0.4)

    logger.info("========== EXIT clickabove() ==========")
    return True

def check_end():
    template = os.path.join(TEMPLATES_DIR, "dead_end.png")
    resize = upscale(template)

    screenshot_view = pyautogui.screenshot()
    screenshot_cv = cv2.cvtColor(np.array(screenshot_view), cv2.COLOR_RGB2GRAY)

    result = cv2.matchTemplate(screenshot_cv, resize, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.8:
        return True


def get_to_final_step(cx, cy, offset_x, offset_y, max_steps=13):
    pyautogui.scroll(-25)
    probe_x = 175
    probe_y = 125
    pyautogui.moveTo(probe_x, probe_y, duration=0.1)
    time.sleep(0.2)

    for i in range(max_steps):
        px, py = capture_view_play(probe_x, probe_y)

        if px is None or py is None:
            logger.info(f"[INFO] step {i+1}: no play at probe ({probe_x}, {probe_y}), moving probe down")
            probe_y += 35
            pyautogui.moveTo(probe_x, probe_y, duration=0.08)
            time.sleep(0.25)
            probe_y += 15
            pyautogui.moveTo(probe_x, probe_y, duration=0.08)
            time.sleep(0.35)
            continue

        play_cx, play_cy = px, py

        logger.info(f"[INFO] step {i+1}: found play at ({play_cx}, {play_cy}), clicking...")
        click_twice(play_cx, play_cy)
        time.sleep(3)

        click_open_camera(initial=False)
        time.sleep(1.5)

        logger.info(f"[INFO] step {i+1}: re-clicking play at ({play_cx}, {play_cy})")
        click_twice(play_cx, play_cy)
        time.sleep(1.5)

        probe_y += 25
        pyautogui.moveTo(probe_x, probe_y, duration=0.08)
        time.sleep(0.25)

        probe_y += 8
        pyautogui.moveTo(probe_x, probe_y, duration=0.08)
        time.sleep(0.35)

    check_images_view()
    return True


def click_twice(x, y):
    for i in range(1):
        pyautogui.click(x, y)
        time.sleep(0.2)


def capture_view_play(x, y,crop_h=45, threshold=0.4, right_margin=40, template_name="play_button.png"):
    screen_w, screen_h = pyautogui.size()

    cx = int(x)
    cy = int(y)

    left = 0
    top = max(0, cy - crop_h // 2)
    right = min(screen_w, cx + int(right_margin))

    w = max(1, int(right - left))
    h = min(int(crop_h), max(1, screen_h - top))
    if w <= 0 or h <= 0:
        return None, None

    screenshot = pyautogui.screenshot(region=(left, top, w, h))
    crop_gray = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2GRAY)

    tpl_path = os.path.join(TEMPLATES_DIR, template_name)
    tpl = cv2.imread(tpl_path, cv2.IMREAD_GRAYSCALE)
    if tpl is None:
        return None, None

    crop_bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    cv2.imwrite(get_screenshot_path("debug_play_crop"), crop_bgr)

    result = cv2.matchTemplate(crop_gray, tpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    logger.debug(f"play max_val = {max_val}")

    if max_val < threshold:
        return None, None

    tx, ty = max_loc
    th, tw = tpl.shape[:2]
    return left + tx + tw // 2, top + ty + th // 2


def click_open_camera(initial=True):
    template = os.path.join(TEMPLATES_DIR, "camera_open.png")
    resize = upscale(template)

    screenshot_view = pyautogui.screenshot()
    screenshot_cv = cv2.cvtColor(np.array(screenshot_view), cv2.COLOR_RGB2GRAY)

    result = cv2.matchTemplate(screenshot_cv, resize, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if initial is True:
        if max_val >= 0.15:
            x, y = max_loc
            h, w = resize.shape[:2]
            doubleclick(x - 120, y - 120, h, w)
            return True

    for i in range(6):
        screenshot_view = pyautogui.screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot_view), cv2.COLOR_RGB2GRAY)

        result = cv2.matchTemplate(screenshot_cv, resize, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= 0.50:
            x, y = max_loc
            h, w = resize.shape[:2]
            doubleclick(x - 120, y - 120, h, w)
            time.sleep(4)
            image_saved = check_images_view()
            if image_saved:
                return True
        time.sleep(1.5)

    return False


def check_images_view():
    template = os.path.join(TEMPLATES_DIR, "window_close.png")
    resize = upscale(template)

    while True:
        screenshot_view = pyautogui.screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot_view), cv2.COLOR_RGB2GRAY)

        result = cv2.matchTemplate(screenshot_cv, resize, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= 0.50:
            time.sleep(0.5)
            x, y = max_loc
            h, w = resize.shape[:2]
            center = center_cordinates(x, y, h, w)
            pyautogui.click(center[0], center[1])
            return True
        time.sleep(2)

    return False


def capture_list_area(roi_x=None, roi_y=None, roi_w=None, roi_h=None):
    logger.debug("[DEBUG] Capturing list area...")

    try:
        screenshot = pyautogui.screenshot(region=(roi_x, roi_y, roi_w, roi_h))
        bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        logger.debug(f"[DEBUG] Captured shape: {hsv.shape}")
        cv2.imwrite(get_screenshot_path("debug_list_capture"), bgr)

        return hsv, (roi_x, roi_y)

    except Exception as e:
        logger.error(f"[ERROR] Capture failed: {e}")
        return None, None


def find_blue_highlight(hsv_img, offset=(0, 0)):
    if hsv_img is None:
        return None

    logger.debug("[DEBUG] Searching for blue highlight...")

    lower_blue = np.array([85, 80, 120], dtype=np.uint8)
    upper_blue = np.array([115, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv_img, lower_blue, upper_blue)

    logger.debug(f"[DEBUG] Mask pixels: {np.count_nonzero(mask)}")

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    cv2.imwrite(get_screenshot_path("debug_blue_mask"), mask)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    logger.debug(f"[DEBUG] Contours found: {len(contours)}")

    best = None
    best_area = 0

    for c in contours:
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)

        if area > 400 and w > h:
            if area > best_area:
                best_area = area
                best = (x, y, w, h)

    if best is None:
        logger.debug("[DEBUG] No valid highlight found")
        return None

    x, y, w, h = best
    abs_x = x + offset[0]
    abs_y = y + offset[1]

    logger.debug(f"[DEBUG] Highlight at ({abs_x}, {abs_y}), size=({w}, {h})")

    return (abs_x, abs_y, w, h)


def doubleclick(x, y, h, w):
    center = center_cordinates(x, y, h, w)
    for clic in range(3):
        pyautogui.click(center[0], center[1])
        time.sleep(0.2)
    logger.info(f"[CLICKED] Element at {center}")
    logger.debug("clicked")
    return True


def write_to_search(text, x, y, h, w):
    logger.info(f"[TYPING] Writing: {text}")

    text = str(text)
    time.sleep(0.1)

    click(x, y, h, w)
    time.sleep(0.12)

    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.08)
    pyautogui.press("delete")
    time.sleep(0.08)

    splited = text.split("-")
    text = splited[0] + "-" + splited[1][0:3]
    helper_char = splited[1][2:3]

    logger.debug(splited)

    pyperclip.copy(text)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.2)

    # if nudge fails after 4 attempts, retry full search
    for retry in range(2):  # first try + 1 full retry
        if nudge_search_until_result(x, y, h, w, helper_char):
            return True

        logger.info("[RETRY] Re-searching from scratch...")

        click(x, y, h, w)
        time.sleep(0.1)

        pyautogui.hotkey("ctrl", "a")
        time.sleep(0.08)
        pyautogui.press("delete")
        time.sleep(0.08)

        pyperclip.copy(text)
        time.sleep(0.2)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)

    return False


def search_result_shown():
    logger.debug("got to see result in search_result_shown")

    search_result = os.path.join(TEMPLATES_DIR, "search_result.png")
    resized_image = upscale(search_result)

    screenshot_view = pyautogui.screenshot()
    screenshot_cv = cv2.cvtColor(np.array(screenshot_view), cv2.COLOR_RGB2GRAY)

    result = cv2.matchTemplate(screenshot_cv, resized_image, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= 0.65:
        time.sleep(0.5)
        return True

    return False


def nudge_search_until_result(x, y, h, w, helper_char):
    attempts = 0

    while attempts < 4:
        if search_result_shown():
            logger.debug("true")
            return True

        doubleclick(x, y, h, w)
        pyautogui.press("backspace")

        if search_result_shown():
            logger.debug("true")
            return True

        pyautogui.press("end")
        time.sleep(0.08)

        if search_result_shown():
            logger.debug("true")
            return True

        pyautogui.typewrite(helper_char)
        time.sleep(0.25)

        attempts += 1
        logger.info(f"[NUDGE ATTEMPT] {attempts}/4")

    logger.warning("[FAILED] No result after 4 nudge attempts")
    return False


if __name__ == "__main__":
    try:
        search()
        logger.info("✓ Success")
    except Exception as e:
        logger.error(f"✗ Error: {e}")
    finally:
        logger.info("press enter to exit")