import os 
import json
from tkinter import filedialog
import subprocess
import time
import cv2
import pyautogui
import numpy as np
import pygetwindow as gw
from logger_setup import get_logger

logger = get_logger(__name__)

REFRENCE_RESOLUTION=(1366,768)
MATCHING_THRESHOLD=0.8

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, "templates")
TRUECLOUD_NAME = os.path.join(SCRIPT_DIR, "config_file.json")
def get_exe_path():
    path = os.path.exists(TRUECLOUD_NAME)
    if path:
        with open(TRUECLOUD_NAME, "r") as f:
            try:
                path_dict = json.load(f)
                path_loaded = path_dict.get("path_exe", "")

                if os.path.exists(path_loaded):
                    logger.info(f"using saved path: {path_loaded}")
                    return path_loaded
            except Exception as e:
                pass
    
    logger.info("path not found please provide path to truecloud")
    path = filedialog.askopenfilename(
        title="SELECT TRUECLOUD",
        filetypes=[("EXE files", "*.exe"), ("ALL files", "*.*")]
    )
    if not path or not os.path.exists(path):
        raise FileNotFoundError("no valid EXE selected")
    with open(TRUECLOUD_NAME, "w") as f:
        json.dump({"path_exe": path}, f, indent=2)
    logger.info("file path configured")
    return path


def start_app_and_login():
    path_to_cloud = get_exe_path()
    if not path_to_cloud:
        logger.error("error no path found")

    app_process = subprocess.Popen(path_to_cloud)
    logger.info("✓ Application launched successfully")

    time.sleep(5)  # wait for window to appear

    # Bring window to front
    windows = gw.getAllTitles()
    for title in windows:
        if "TRUECLOUD" in title:   # change this to your actual app window title
            win = gw.getWindowsWithTitle(title)[0]
            win.activate()
            logger.info(f"✓ Brought '{title}' to front")
            break

    login = login_click()
    return login

    
def get_scale():
    current_screen=pyautogui.size()
    current_screen_width=current_screen[0]
    refrence_width=REFRENCE_RESOLUTION[0]
    scaling_factor=current_screen_width/refrence_width
    return scaling_factor


def upscale(image_template):
    image=cv2.imread(image_template)
    scale=get_scale()
    resize_image=cv2.resize(image,None,fx=scale,fy=scale,interpolation=cv2.INTER_LINEAR)
    resize_image_grey=cv2.cvtColor(resize_image, cv2.COLOR_BGR2GRAY)
    return resize_image_grey

def center_cordinates(x,y,h,w):
    center_x = x + w // 2
    center_y = y + h // 2
    return (center_x, center_y)


def is_logged_in(timeout=60):
    home = os.path.join(TEMPLATES_DIR, "Home.png")
    resized_image = upscale(home)

    start_time = time.time()

    while time.time() - start_time < timeout:
        screenshot_view = pyautogui.screenshot()
        screenshot_cv = cv2.cvtColor(np.array(screenshot_view), cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(screenshot_cv, resized_image, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)

        if max_val >= MATCHING_THRESHOLD:
            time.sleep(3)
            return True

        time.sleep(0.2)

    return False

def click(x,y,h,w,to=None):
    center=center_cordinates(x,y,h,w)
    pyautogui.click(center[0], center[1])
    logger.info(f"[CLICKED] Element at {center}")
    if to=="login":
       return is_logged_in()
    time.sleep(2)
    logger.debug("clicked")
    return True


def login_click():
    template_path=os.path.join(TEMPLATES_DIR,"login.png")
    resized_image=upscale(template_path)
    screenshot_view = pyautogui.screenshot()
    screenshot_cv = cv2.cvtColor(np.array(screenshot_view),cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(screenshot_cv, resized_image, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val >= MATCHING_THRESHOLD:
        x, y = max_loc
        h, w = resized_image.shape[:2]
    
        clicked=click(x,y,h,w,to="login")
        if clicked:
            logger.info("logging success full!")
            return True
    return False


