import os 
import json
from tkinter import filedialog
import subprocess
import time
import cv2
import pyautogui
import numpy as np
import pyperclip

from truecloud import start_app_and_login,TEMPLATES_DIR,upscale,MATCHING_THRESHOLD,click,center_cordinates,SCRIPT_DIR
ITEMS = ["NAIPURA,01-PANWARI","BUDHAURA,01-JAITHPUR", "BANDO,02-PANWARI"]

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

            for item in ITEMS:
                
                click(x, y, h, w)
                time.sleep(0.15)

                write_to_search(item, x, y, h, w)
                clickbelow(x, y, h, w)
                clickabove(x, y, h, w)
                time.sleep(1)

            return True

    except Exception:
        pass

def clickbelow(x, y, h, w):
    center = center_cordinates(x, y, h, w)
    pyautogui.click(center[0], center[1] + 20) 

def clickabove(x, y, h, w):
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

    if 20 <= abs(dx) <= 50 and abs(dy) <= 40:
        offset_x, offset_y = 80, +8
        print("[INFO] Using alternate offset")
    else:
        offset_x, offset_y = 95, -4
        print("[INFO] Using default offset")

    pyautogui.click(cx + offset_x, cy + offset_y)
    return True

def get_playcoordinates():
    play=os.path.join(TEMPLATES_DIR,"play_button.png")
    image=cv2.imread(play)
    scaled=upscale(image)

    screenshot_view = pyautogui.screenshot()
    screenshot_cv = cv2.cvtColor(np.array(screenshot_view),cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(screenshot_cv, scaled, cv2.TM_CCOEFF_NORMED)
    _,max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= 0.5:
        x, y = max_loc
        h, w = scaled.shape[:2]
        return x,y,h,w
    return None,None,None,None


def capture_list_area(roi_x=None, roi_y=None, roi_w=None, roi_h=None):
    print(f"[DEBUG] Capturing list area...")

    try:
        screenshot = pyautogui.screenshot(region=(roi_x, roi_y, roi_w, roi_h))
        bgr = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

        print(f"[DEBUG] Captured shape: {hsv.shape}")

        # Debug save
        cv2.imwrite(os.path.join(SCRIPT_DIR, "debug_list_capture.png"), bgr)

        return hsv, (roi_x, roi_y)

    except Exception as e:
        print(f"[ERROR] Capture failed: {e}")
        return None, None
    

def find_blue_highlight(hsv_img, offset=(0, 0)):
    if hsv_img is None:
        return None

    print("[DEBUG] Searching for blue highlight...")

    lower_blue = np.array([85, 80, 120], dtype=np.uint8)
    upper_blue = np.array([115, 255, 255], dtype=np.uint8)

    mask = cv2.inRange(hsv_img, lower_blue, upper_blue)

    print(f"[DEBUG] Mask pixels: {np.count_nonzero(mask)}")

    # Clean noise
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # Save mask for debug
    cv2.imwrite(os.path.join(SCRIPT_DIR, "debug_blue_mask.png"), mask)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    print(f"[DEBUG] Contours found: {len(contours)}")

    best = None
    best_area = 0

    for c in contours:
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)

        if area > 400 and w > h:  # horizontal row shape
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


def doubleclick(x,y,h,w):
    center=center_cordinates(x,y,h,w)
    for clic in range(3):
        pyautogui.click(center[0], center[1])
        time.sleep(0.2)
    print(f"[CLICKED] Element at {center}")
    print("clicked")
    return True


def write_to_search(text,x,y,h,w):
    print(f"[TYPING] Writing: {text}")

    text = str(text)
    time.sleep(0.1)

    click(x, y, h, w)
    time.sleep(0.12)

    pyautogui.hotkey("ctrl", "a") 
    time.sleep(0.08)
    pyautogui.press("delete")
    time.sleep(0.08)

    splited=text.split("-")
    text=splited[0] +"-" + splited[1][0:3]
    helper_char=splited[1][2:3]

    print(splited)
    pyperclip.copy(text)
    time.sleep(0.2)
    pyautogui.hotkey("ctrl","v")
    time.sleep(0.2)

    nudge_search_until_result(x,y,h,w,helper_char)
    
    return True

def search_result_shown():
    print("got to see result in search_result_shown")
    search_result=os.path.join(TEMPLATES_DIR,"search_result.png")
    resized_image=upscale(search_result)

    screenshot_view = pyautogui.screenshot()

    screenshot_cv = cv2.cvtColor(np.array(screenshot_view),cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(screenshot_cv, resized_image, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= 0.5:
        return True
    return False

def nudge_search_until_result(x, y, h, w, helper_char):
    while True:
        if search_result_shown():
            print("true")
            return True

        doubleclick(x, y, h, w)
        pyautogui.press("backspace")

        if search_result_shown():
            print("true")
            return True

        pyautogui.press("end")
        time.sleep(0.08)

        if search_result_shown():
            print("true")
            return True
        
        pyautogui.typewrite(helper_char)
        time.sleep(0.25)
    return False

if __name__ == "__main__":
    try:
        search()
        print(f"✓ Success")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        print("press enter to exit")