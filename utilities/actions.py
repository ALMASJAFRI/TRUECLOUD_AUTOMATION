import os
import time
import cv2
import numpy as np
import pyautogui
import pyperclip

from truecloud import TEMPLATES_DIR, upscale, click, center_cordinates
from utilities.detection import search_result_shown, check_images_view

VERBOSE_LOGS = False


def log(message):
    if VERBOSE_LOGS:
        print(message)


def click_twice(x, y):
    for i in range(2):
        pyautogui.click(x, y)
        time.sleep(0.2)


def doubleclick(x, y, h, w):
    center = center_cordinates(x, y, h, w)
    for clic in range(3):
        pyautogui.click(center[0], center[1])
        time.sleep(0.2)
    log(f"[CLICKED] Element at {center}")
    log("clicked")
    return True


def clickbelow(x, y, h, w):
    center = center_cordinates(x, y, h, w)
    pyautogui.click(center[0], center[1] + 20)


def click_open_camera(initial=True):
    template = os.path.join(TEMPLATES_DIR, "camera_open.png")
    resize = upscale(template)

    screenshot_view = pyautogui.screenshot()
    screenshot_cv = cv2.cvtColor(np.array(screenshot_view), cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(screenshot_cv, resize, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if initial == True:
        if max_val >= 0.15:
            x, y = max_loc
            h, w = resize.shape[:2]
            doubleclick(x - 120, y - 120, h, w)
            return True
    if max_val >= 0.15:
        x, y = max_loc
        h, w = resize.shape[:2]
        doubleclick(x - 120, y - 120, h, w)
        time.sleep(4)
        image_saved = check_images_view()
        if image_saved:
            return True

    return False


def write_to_search(text, x, y, h, w):
    log(f"[TYPING] Writing: {text}")

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

    log(splited)
    pyperclip.copy(text)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.2)

    nudge_search_until_result(x, y, h, w, helper_char)

    return True


def nudge_search_until_result(x, y, h, w, helper_char):
    while True:
        if search_result_shown():
            log("true")
            return True

        doubleclick(x, y, h, w)
        pyautogui.press("backspace")

        if search_result_shown():
            log("true")
            return True

        pyautogui.press("end")
        time.sleep(0.08)

        if search_result_shown():
            log("true")
            return True

        pyautogui.typewrite(helper_char)
        time.sleep(0.25)
    return False
