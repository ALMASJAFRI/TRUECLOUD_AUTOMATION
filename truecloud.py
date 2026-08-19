import os 
import json
from tkinter import filedialog
import subprocess
import time
import cv2
import pyautogui
import numpy as np

REFRENCE_RESOLUTION=(1920,1080)
MATCHING_THRESHOLD=0.8
AFTER_LOGIN_DELAY=0.2
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SCRIPT_DIR, "templates")
TRUECLOUD_NAME = os.path.join(SCRIPT_DIR, "config_file.json")

def set_After_Login_Delay(value):
    global AFTER_LOGIN_DELAY
    AFTER_LOGIN_DELAY=value
    

def get_exe_path():
    path = os.path.exists(TRUECLOUD_NAME)
    if path:
        with open(TRUECLOUD_NAME, "r") as f:
            try:
                path_dict = json.load(f)
                path_loaded = path_dict.get("path_exe", "")

                if os.path.exists(path_loaded):
                    print(f"using saved path: {path_loaded}")
                    return path_loaded
            except Exception as e:
                pass
    
    print("path not found please provide path to truecloud")
    path = filedialog.askopenfilename(
        title="SELECT TRUECLOUD",
        filetypes=[("EXE files", "*.exe"), ("ALL files", "*.*")]
    )
    if not path or not os.path.exists(path):
        raise FileNotFoundError("no valid EXE selected")
    with open(TRUECLOUD_NAME, "w") as f:
        json.dump({"path_exe": path}, f, indent=2)
    print(f"file path configured")
    return path
def start_app_and_login():
    path_to_cloud=get_exe_path()
    if not path_to_cloud:
        print("error no path found")
    open=subprocess.Popen(path_to_cloud)
    print("✓ Application launched successfully")
    time.sleep(4)  
    login=login_click()
    if login:
       return True
    else:
        return False

    
def get_scale() -> float:
    current_screen = pyautogui.size()
    current_screen_width = int(current_screen[0])

    reference_width = int(REFRENCE_RESOLUTION[0])

    return float(current_screen_width / reference_width)


def upscale(image_template: str):
    image = cv2.imread(image_template)

    if image is None:
        return None

    scale: float = get_scale()

    height, width = image.shape[:2]

    new_width: int = int(width * scale)
    new_height: int = int(height * scale)

    resize_image = cv2.resize(
        image,
        (new_width, new_height),
        interpolation=cv2.INTER_LINEAR
    )

    resize_image_grey = cv2.cvtColor(
        resize_image,
        cv2.COLOR_BGR2GRAY
    )

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
            return True
        time.sleep(AFTER_LOGIN_DELAY)

    return False

def click(x,y,h,w,to=None):
    center=center_cordinates(x,y,h,w)
    pyautogui.click(center[0], center[1])
    print(f"[CLICKED] Element at {center}")
    if to=="login":
       return is_logged_in()
    time.sleep(2)
    print("clicked")
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
            print("logging success full!")
            return True
    return False


#8189034475
#Test@123