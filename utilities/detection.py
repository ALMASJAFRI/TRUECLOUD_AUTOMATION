import os
import time
import cv2
import numpy as np
import pyautogui

from truecloud import TEMPLATES_DIR, upscale, center_cordinates


def find_blue_highlight(hsv_img, offset=(0, 0)):
    if hsv_img is None:
        return None

    print("[DEBUG] Searching for blue highlight...")

    lower_blue = np.array([85, 80, 120], dtype=np.uint8)
    upper_blue = np.array([115, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv_img, lower_blue, upper_blue)

    print(f"[DEBUG] Mask pixels: {np.count_nonzero(mask)}")

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    print(f"[DEBUG] Contours found: {len(contours)}")

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
        print("[DEBUG] No valid highlight found")
        return None

    x, y, w, h = best
    abs_x = x + offset[0]
    abs_y = y + offset[1]

    print(f"[DEBUG] Highlight at ({abs_x}, {abs_y}), size=({w},{h})")

    return (abs_x, abs_y, w, h)


def search_result_shown():
    print("got to see result in search_result_shown")
    search_result = os.path.join(TEMPLATES_DIR, "search_result.png")
    resized_image = upscale(search_result)

    screenshot_view = pyautogui.screenshot()

    screenshot_cv = cv2.cvtColor(np.array(screenshot_view), cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(screenshot_cv, resized_image, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= 0.65:
        time.sleep(0.5)
        return True
    return False


def check_end():
    template = os.path.join(TEMPLATES_DIR, "dead_end.png")
    resize = upscale(template)

    screenshot_view = pyautogui.screenshot()
    screenshot_cv = cv2.cvtColor(np.array(screenshot_view), cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(screenshot_cv, resize, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.8:
        return True


def check_images_view():
    template = os.path.join(TEMPLATES_DIR, "window_close.png")
    resize = upscale(template)

    while True:
        screenshot_view = pyautogui.screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot_view), cv2.COLOR_BGR2GRAY)

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
