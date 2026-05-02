# UI Automation Plan - MedGenX

**Objective:** Automate UI interactions by combining **OpenCV** (vision detection) and **PyAutoGUI** (action execution).

---

## 🧠 Core Concept

| Component | Purpose | Output |
|-----------|---------|--------|
| **OpenCV** | Finds UI elements on screen | Position coordinates `(x, y, width, height)` |
| **PyAutoGUI** | Executes clicks, typing, and navigation | Performs actual user actions |
| **Flow Controller** | Coordinates the sequence | Ensures proper timing and retry logic |

**One-sentence summary:** Vision finds it → Automation does it.

---

## 🔷 Phase 0: Application Launch & Configuration

### 0.1 Smart EXE Path Resolver

Automatically detects or saves the application path—works on any machine:


```python
import os
import json
from tkinter import filedialog
import subprocess
import time

CONFIG_FILE = "config.json"

def get_exe_path():
    """
    Smart path resolver - tries 3 strategies:
    1. Check bundled local app.exe
    2. Load from saved config.json
    3. Ask user (only once)
    """
    # Strategy 1: Check local folder
    local_path = os.path.join(os.path.dirname(__file__), "app.exe")
    if os.path.exists(local_path):
        print(f"✓ Found local EXE: {local_path}")
        return local_path

    # Strategy 2: Check saved config
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                data = json.load(f)
                saved_path = data.get("exe_path", "")
                if os.path.exists(saved_path):
                    print(f"✓ Using saved path: {saved_path}")
                    return saved_path
            except json.JSONDecodeError:
                pass

    # Strategy 3: Ask user (first run only)
    print("\n⚠ EXE not found. Please select the application...")
    path = filedialog.askopenfilename(
        title="Select Application EXE",
        filetypes=[("EXE files", "*.exe"), ("All files", "*.*")]
    )

    if not path or not os.path.exists(path):
        raise FileNotFoundError("No valid EXE selected")

    # Save for future runs (no dialog next time)
    with open(CONFIG_FILE, "w") as f:
        json.dump({"exe_path": path}, f, indent=2)
    
    print(f"✓ Configuration saved to {CONFIG_FILE}")
    return path


def launch_app():
    """
    Launch application before automation starts
    
    Returns:
        True if successful, False otherwise
    """
    try:
        exe_path = get_exe_path()
        print(f"\n[PHASE 0] Launching: {exe_path}")
        subprocess.Popen(exe_path)
        print("✓ Application launched successfully")
        time.sleep(3)  # Wait for app to fully initialize
        return True
    except Exception as e:
        print(f"✗ Failed to launch app: {e}")
        return False
```

### 0.2 Project Structure

```
project/
├── bot.py (main automation script)
├── config.json (auto-created on first run)
├── app.exe (optional - if bundled)
├── templates/ (required - reference images)
│   ├── input.png (search field)
│   ├── loop.png (loop button)
│   ├── next.png (next button)
│   ├── success.png (success indicator)
│   └── error.png (error dialog)
└── logs/ (optional - debug output)
```

### 0.3 First Run Behavior

| Run # | Dialog? | Behavior |
|-------|---------|----------|
| **1st** | ✓ YES | User selects EXE, saved to config.json |
| **2nd+** | ✗ NO | Auto-loads from config.json, no dialog |
| **Bundled** | ✗ NO | Auto-detects app.exe in same folder |

---

## 🔷 Phase 1: Detection Pipeline

### 1.1 Template Image Capture

Before automation starts, capture reference templates:


```


Templates needed:
├── next_button.png (Next button icon)
├── loop_button.png (Loop/Refresh button)
├── search_input.png (Input field anchor)
├── error_dialog.png (Error message visual)
└── success_indicator.png (Success marker)
```


**How to capture:**
- Use screenshot tool or `pyautogui.screenshot()`
- Keep templates 50-200 pixels
- Capture at same resolution as target environment


### 1.2 Template Matching Function

```python
import cv2
import numpy as np
from pyautogui import locateOnScreen

def find_template(template_path, threshold=0.8):
    """
    Find template image on screen
    
    Args:
        template_path: Path to template image
        threshold: Match confidence (0.8 = 80%)
    
    Returns:
        Tuple (x, y, width, height) or None
    """
    screenshot = pyautogui.screenshot()
    screenshot_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    template = cv2.imread(template_path)
    
    result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    if max_val >= threshold:
        x, y = max_loc
        h, w = template.shape[:2]
        return (x, y, w, h)
    return None
```


### 1.3 Convert Detection to Clickable Point

```python
def get_center(detection):
    """
    Convert template detection to center point
    
    Args:
        detection: Tuple (x, y, width, height)
    
    Returns:
        Tuple (center_x, center_y)
    """
    if detection is None:
        return None
    x, y, w, h = detection
    center_x = x + w // 2
    center_y = y + h // 2
    return (center_x, center_y)
```

---

## 🔷 Phase 2: Action Execution

### 2.1 Click Action

```python
def click_element(template_path, threshold=0.8):
    """Click center of detected template"""
    detection = find_template(template_path, threshold)
    if detection:
        center = get_center(detection)
        pyautogui.click(center[0], center[1])
        return True
    return False
```

### 2.2 Text Input Action

```python
def input_text(template_path, text, clear_first=True):
    """
    Click text field and enter text
    
    Args:
        template_path: Input field reference image
        text: Text to enter
        clear_first: Whether to clear existing text
    """
    if click_element(template_path):
        time.sleep(0.5)  # Wait for focus
        
        if clear_first:
            pyautogui.hotkey("ctrl", "a")  # Select all
            pyautogui.press("backspace")   # Delete
            time.sleep(0.3)
        
        pyautogui.write(text)  # Type new text
        return True
    return False
```

### 2.3 Navigate Action (Next/Previous)

```python
def click_navigation(button_type="next"):
    """
    Click navigation buttons
    
    Args:
        button_type: "next", "prev", "loop"
    
    Returns:
        True if successful
    """
    button_map = {
        "next": "templates/next_button.png",
        "prev": "templates/prev_button.png",
        "loop": "templates/loop_button.png"
    }
    return click_element(button_map[button_type])
```

---

## 🔷 Phase 3: Robust Waiting Logic

### 3.1 Wait for UI Element

```python
def wait_for_element(template_path, timeout=10, poll_interval=0.5):
    """
    Wait for element to appear on screen
    
    Args:
        template_path: Element to wait for
        timeout: Max wait time (seconds)
        poll_interval: How often to check (seconds)
    
    Returns:
        Detection tuple if found, None if timeout
    """
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        detection = find_template(template_path, threshold=0.8)
        if detection:
            print(f"✓ Found {template_path}")
            return detection
        
        time.sleep(poll_interval)
    
    print(f"✗ Timeout waiting for {template_path}")
    return None
```

### 3.2 Conditional Wait (Error/Success Detection)

```python
def wait_for_result(timeout=15):
    """
    Wait for operation result (Error or Success)
    
    Returns:
        "success" | "error" | "timeout"
    """
    import time
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        # Check for error dialog
        if find_template("templates/error_dialog.png"):
            print("✗ Error detected")
            return "error"
        
        # Check for success indicator
        if find_template("templates/success_indicator.png"):
            print("✓ Success detected")
            return "success"
        
        time.sleep(1)
    
    return "timeout"
```

---

## 🔷 Phase 4: Main Automation Flow

### 4.1 Standard Search Workflow

```python
def automate_search(device_name, loop_count=1, wait_seconds=5):
    """
    Full automation sequence for device search
    
    Flow:
        1. Wait for app ready
        2. Select loop mode
        3. Set search parameters
        4. Execute search
        5. Wait for result
    """
    
    print("[Step 1] Waiting for app to load...")
    if not wait_for_element("templates/search_input.png", timeout=10):
        print("App failed to load")
        return False
    
    time.sleep(1)
    
    print("[Step 2] Clicking Loop button...")
    if not click_element("templates/loop_button.png"):
        print("Failed to click loop button")
        return False
    
    time.sleep(0.5)
    
    print("[Step 3] Setting loop count...")
    # Click loop count input
    if not input_text("templates/loop_input.png", str(loop_count)):
        print("Failed to set loop count")
        return False
    
    time.sleep(0.5)
    
    print("[Step 4] Setting wait seconds...")
    if not input_text("templates/wait_input.png", str(wait_seconds)):
        print("Failed to set wait time")
        return False
    
    time.sleep(0.5)
    
    print("[Step 5] Entering search device name...")
    if not input_text("templates/search_input.png", device_name):
        print("Failed to enter device name")
        return False
    
    time.sleep(0.5)
    
    print("[Step 6] Clicking Next button...")
    if not click_element("templates/next_button.png"):
        print("Failed to click next button")
        return False
    
    print("[Step 7] Waiting for result...")
    result = wait_for_result(timeout=30)
    
    if result == "success":
        print("✓ Automation completed successfully")
        return True
    elif result == "error":
        print("✗ Search returned error")
        return False
    else:
        print("✗ Operation timed out")
        return False
```

### 4.2 Retry Logic

```python
def automate_search_with_retry(device_name, max_retries=3):
    """
    Execute automation with retry on failure
    """
    for attempt in range(1, max_retries + 1):
        print(f"\n[Attempt {attempt}/{max_retries}]")
        
        success = automate_search(device_name)
        
        if success:
            print(f"✓ Success on attempt {attempt}")
            return True
        
        print(f"✗ Failed on attempt {attempt}")
        
        if attempt < max_retries:
            print("Retrying in 3 seconds...")
            time.sleep(3)
    
    print(f"✗ Failed after {max_retries} attempts")
    return False
```

---

## 🔷 Phase 5: Error Handling & Recovery

### 5.1 Detection Failure

```python
def robust_click(template_path, retries=3, threshold=0.8):
    """
    Click with fallback detection
    
    Tries:
    1. High confidence match (0.8)
    2. Medium confidence match (0.7)
    3. Low confidence match (0.6)
    """
    thresholds = [0.8, 0.7, 0.6]
    
    for threshold in thresholds:
        if click_element(template_path, threshold):
            print(f"✓ Clicked with {threshold*100}% confidence")
            return True
    
    print(f"✗ Could not find {template_path}")
    return False
```

### 5.2 Timeout Handling

```python
def safe_operation(operation_func, timeout=20):
    """
    Wrap operation with timeout protection
    
    Prevents infinite hangs
    """
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation exceeded {timeout} seconds")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    
    try:
        result = operation_func()
        signal.alarm(0)  # Cancel alarm
        return result
    except TimeoutError as e:
        print(f"⚠ {e}")
        return False
```

---

## 🔷 Phase 6: Resolution & UI Variations

### 6.1 Multi-Template Fallback

```python
def find_any_template(template_paths, threshold=0.8):
    """
    Try multiple templates (for UI variations)
    
    Returns:
        (detection, matched_template_path) or (None, None)
    """
    for template_path in template_paths:
        detection = find_template(template_path, threshold)
        if detection:
            return detection, template_path
    return None, None
```

### 6.2 Anchor-Based Detection

```python
def find_relative_to_anchor(anchor_template, offset_x, offset_y):
    """
    Find elements relative to anchor position
    
    Useful for layouts that shift but maintain relative positions
    
    Args:
        anchor_template: Reference element
        offset_x, offset_y: Relative coordinates from anchor
    
    Returns:
        Absolute position or None
    """
    anchor = find_template(anchor_template)
    if anchor:
        x, y, w, h = anchor
        return (x + offset_x, y + offset_y)
    return None
```

---

## 📋 Implementation Checklist

- [ ] Create `templates/` directory with reference images
- [ ] Implement template matching functions
- [ ] Implement action functions (click, type, navigate)
- [ ] Implement waiting functions with timeouts
- [ ] Create main automation flow
- [ ] Add error handling and retries
- [ ] Test each function independently
- [ ] Test full workflow end-to-end
- [ ] Document template locations and names
- [ ] Create logging for debugging

---

## ⚠️ Known Limitations & Workarounds

| Issue | Cause | Solution |
|-------|-------|----------|
| Template not found | Threshold too high or UI changed | Lower threshold or update template |
| Clicks wrong button | Multiple similar items | Use anchor-relative detection |
| Hangs indefinitely | No timeout on wait | Always use timeout parameter |
| Works on one resolution, breaks on another | Template size mismatch | Capture at target resolution |
| Text entry fails | Input field not focused | Add longer sleep after click |

---

## 🚀 Example Usage

```python
# Most Basic - Single search with automatic app launch
def run_automation(device_name):
    """Complete automation from app launch to result"""
    
    # Phase 0: Launch app first
    if not launch_app():
        print("Failed to launch app")
        return False
    
    # Phase 1: Wait for UI to appear
    if not wait_for_element("templates/input.png", timeout=15):
        print("App UI not detected")
        return False
    
    time.sleep(1)
    
    # Phase 2: Click and interact
    click_element("templates/loop.png")
    time.sleep(0.5)
    
    # Phase 2: Input text
    if click_element("templates/input.png"):
        time.sleep(0.5)
        pyautogui.hotkey("ctrl", "a")  # Select all
        pyautogui.press("backspace")   # Clear
        pyautogui.write(device_name)   # Type new text
    
    time.sleep(0.5)
    
    # Phase 2: Click next
    click_element("templates/next.png")
    
    # Phase 3: Wait for result
    result = wait_for_result(timeout=30)
    
    if result == "success":
        print("✓ Automation completed successfully")
        return True
    elif result == "error":
        print("✗ Search returned error")
        return False
    else:
        print("✗ Operation timed out")
        return False


# With automatic retries
def run_automation_with_retries(device_name, max_retries=3):
    """Run automation with automatic retry on failure"""
    for attempt in range(1, max_retries + 1):
        print(f"\n[Attempt {attempt}/{max_retries}]")
        
        if run_automation(device_name):
            return True
        
        print(f"Retrying in 3 seconds...")
        time.sleep(3)
    
    print(f"Failed after {max_retries} attempts")
    return False


# Batch processing multiple devices
devices = ["Samsung Galaxy S21", "iPhone 14", "Pixel 7"]
for device in devices:
    print(f"\n{'='*50}")
    print(f"Processing: {device}")
    print(f"{'='*50}")
    success = run_automation_with_retries(device, max_retries=2)
    if success:
        print(f"✓ {device}: SUCCESS")
    else:
        print(f"✗ {device}: FAILED")
    time.sleep(2)  # Pause between devices
```

### Key Points

✅ **App launches automatically** before automation starts  
✅ **No hardcoded paths** - saved to config.json  
✅ **First run only** - user selects EXE once  
✅ **Scheduled runs** - no dialogs, runs silently  
✅ **Retries automatically** - robust against failures  

---

## 📊 Debug Mode

```python
def automate_search_debug(device_name):
    """
    Run with visual feedback and detailed logging
    """
    import logging
    
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    logger.debug(f"Starting search for: {device_name}")
    
    # Take screenshot for inspection
    screenshot = pyautogui.screenshot()
    screenshot.save(f"debug_{device_name}.png")
    logger.debug(f"Screenshot saved: debug_{device_name}.png")
    
    # Run with all intermediate steps logged
    result = automate_search(device_name)
    
    logger.info(f"Result: {result}")
    return result
```

---

## 📚 Dependencies

```
opencv-python==4.8.0
python-autogui==0.9.53
pillow==10.0.0
numpy==1.24.0
```

---

## 🔗 Architecture Diagram

```
┌─────────────────────────────────────────┐
│     UI Automation Pipeline              │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐                       │
│  │  Screenshot  │                       │
│  └──────┬───────┘                       │
│         │                               │
│         ▼                               │
│  ┌──────────────────────┐               │
│  │  Template Matching   │               │
│  │  (OpenCV)            │               │
│  └──────┬───────────────┘               │
│         │                               │
│         ▼                               │
│  ┌──────────────────────┐               │
│  │  Get Coordinates     │               │
│  │  (x, y, w, h)        │               │
│  └──────┬───────────────┘               │
│         │                               │
│         ▼                               │
│  ┌──────────────────────┐               │
│  │  Calculate Center    │               │
│  │  (cx, cy)            │               │
│  └──────┬───────────────┘               │
│         │                               │
│         ▼                               │
│  ┌──────────────────────┐               │
│  │  Execute Action      │               │
│  │  Click/Type/etc      │               │
│  │  (PyAutoGUI)         │               │
│  └──────┬───────────────┘               │
│         │                               │
│         ▼                               │
│  ┌──────────────────────┐               │
│  │  Wait for Result     │               │
│  │  Error/Success/etc   │               │
│  └──────────────────────┘               │
│                                         │
└─────────────────────────────────────────┘
```

---

**Last Updated:** April 2026
**Status:** Ready for Implementation
