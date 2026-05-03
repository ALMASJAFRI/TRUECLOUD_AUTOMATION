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
ITEMS = ["NAIPURA,01-PANWARI"]

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

def clickbelow(x, y, h, w):
    center = center_cordinates(x, y, h, w)
    pyautogui.click(center[0], center[1] + 20) 


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
    seen=set()

    while True:
        px, py = capture_view_play(cx + offset_x, cy + offset_y)

        if px is None or py is None:
            print("[INFO] No more play buttons found, exiting loop")
            print("[INFO] Scrolling down 50px")
            pyautogui.scroll(-25)  
            time.sleep(0.5)
            continue
        
        if not (px,py) in seen:

            play_cx = px
            play_cy = py 
            
            print(f"[INFO] Found play button at ({play_cx}, {play_cy}), clicking...")
            pyautogui.click(play_cx, play_cy)
            time.sleep(3)
            
            click_open_camera(initial=False)
            time.sleep(1.5)
            
            print(f"[INFO] Re-clicking play button at ({play_cx}, {play_cy})")
            pyautogui.click(play_cx, play_cy)
            time.sleep(1.5)

            print("[INFO] Scrolling down 50px")
            pyautogui.scroll(-25)  
            time.sleep(0.5)  
            seen.add((px,py))
        pyautogui.scroll(-10)  
        time.sleep(0.5)  
    return True
        


def capture_view_play(x, y, size=100, threshold=0.6, template_name="play_button.png",first=False):
    
    size = int(size)
    screen_w,screen_h=pyautogui.size()
    shift = -10
    top_trim = max(4, size // 12)
    bottom_trim = max(12, size // 4)

    left = max(0, x - size // 2)
    top = max(0, y - size // 2 + shift + top_trim)

    width = size
    height = max(1, size - top_trim - bottom_trim)

    w = min(width, screen_w - left)
    h = min(height, screen_h - top)
    
    if w <= 0 or h <= 0:
        return None, None

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

    cv2.imwrite(os.path.join(SCRIPT_DIR, "debug_play_crop.png"), crop_bgr)

    if first:
        tx, ty = max_loc
        th, tw = tpl_gray.shape[:2]
        abs_cx = left + tx + tw // 2
        abs_cy = top + ty + th // 2
        return abs_cx, abs_cy


    if max_val >= threshold:
        tx, ty = max_loc
        th, tw = tpl_gray.shape[:2]
        abs_cx = left + tx + tw // 2
        abs_cy = top + ty + th // 2
        return abs_cx, abs_cy
    
    return None, None

def click_open_camera(initial=True):
    template=os.path.join(TEMPLATES_DIR,"camera_open.png")
    resize=upscale(template)

    screenshot_view = pyautogui.screenshot()
    screenshot_cv = cv2.cvtColor(np.array(screenshot_view), cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(screenshot_cv, resize, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if initial==True:
        if max_val >= 0.15:
            x, y = max_loc
            h, w = resize.shape[:2]
            doubleclick(x-120,y-120,h,w)
            return True
    if max_val >=0.15:
        x, y = max_loc
        h, w = resize.shape[:2]
        doubleclick(x-120,y-120,h,w)
        time.sleep(4)
        image_saved=check_images_view()
        if image_saved:
          return True
        
    return False


def check_images_view():
    template=os.path.join(TEMPLATES_DIR,"window_close.png")
    resize=upscale(template)

    while True:
        screenshot_view = pyautogui.screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot_view), cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(screenshot_cv, resize, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >=0.50:
            time.sleep(0.5)
            x, y = max_loc
            h, w = resize.shape[:2]
            center=center_cordinates(x,y,h,w)
            pyautogui.click(center[0], center[1])    
            return True
        time.sleep(2)
    return False

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

    
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    cv2.imwrite(os.path.join(SCRIPT_DIR, "debug_blue_mask.png"), mask)

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

    if max_val >= 0.65:
        time.sleep(0.5)
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