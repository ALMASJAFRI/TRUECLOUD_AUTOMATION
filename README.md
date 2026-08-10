# TrueCloud Automation
Desktop automation for TrueCloud camera search and preview workflows using computer vision and UI control in Python.

## Overview
MedGenX automates repetitive TrueCloud operator actions such as launching the application, logging in, searching camera labels, selecting highlighted results, and opening playback or camera views. It is designed for repetitive operational checks where consistency and speed are critical.

## Problem Statement

Manual camera validation in TrueCloud is time-intensive and prone to inconsistency:

- Repeated login and navigation steps increase operator fatigue.
- Search input behavior can be unstable due to focus and rendering delays.
- Small UI changes and resolution differences can break fixed-coordinate scripts.
- Visual confirmation steps are difficult to scale across many camera entries.

This project solves these issues with template-based detection, resolution-aware scaling, controlled retries, and deterministic item processing.

## Key Features

- Automatic TrueCloud launch with persistent executable path configuration.
- First-run executable selection via file picker, then saved in `config_file.json`.
- Login automation with post-click home-screen verification.
- Resolution-aware template matching based on a reference screen size.
- Deterministic processing of configured camera search items.
- Search stabilization strategy using focus reset, clear, paste, and typed nudge logic.
- Blue-highlight row detection in HSV color space for reliable selection.
- Local region-of-interest play-button detection to reduce false matches and compute load.
- Debug image outputs (`debug_*.png`) for troubleshooting template and detection issues.

## Tech Stack

- Python 3
- OpenCV (`cv2`) and NumPy for image processing and template matching
- PyAutoGUI and Pyperclip for desktop automation and input handling
- Tkinter `filedialog` for executable path selection
- Standard library modules: `os`, `json`, `subprocess`, `time`

## Repository Structure

- `runsearching.py` - main workflow orchestration for item search and camera view actions.
- `truecloud.py` - application startup, login process, scaling helpers, and click utilities.
- `templates/` - UI reference templates used by image matching.
- `config_file.json` - persistent TrueCloud executable path.
- `logs/`, `log.txt` - runtime and related integration logs.
- `envt/` - local virtual environment.

## Getting Started

### Prerequisites

- Windows environment
- Python 3.10+ recommended
- Installed TrueCloud desktop application
- TrueCloud UI templates available in `templates/`

### Installation

```powershell
.\envt\Scripts\Activate.ps1
pip install opencv-python pyautogui numpy pyperclip pillow
```

### Run

```powershell
python runsearching.py
```

On first run, choose the TrueCloud executable when prompted. The selected path is stored in `config_file.json`.

## Configuration

- Search targets are currently defined in the `ITEMS` list inside `runsearching.py`.
- Matching thresholds are defined in code (`MATCHING_THRESHOLD` and feature-specific thresholds).
- Reference resolution is configured as `1920x1080` and used to scale templates at runtime.

## Complexities Handled

### 1. Resolution and DPI Variations

Fixed coordinates are fragile across displays. The project rescales templates based on current screen width relative to a reference resolution before matching.

### 2. UI Focus Instability During Search

Typing reliability is improved by explicitly restoring focus, clearing existing input, pasting normalized text, and nudging the query when result detection is delayed.

### 3. Visual Noise and False Positives

Blue highlight detection uses HSV masking, morphological cleanup, and contour filtering by area and shape to isolate valid candidate rows.

### 4. Asynchronous UI State Changes

The flow combines timed waits with state polling (login success, search result visibility, camera panel checks) to reduce race conditions.

### 5. Matching Cost and Runtime Efficiency

Expensive full-screen matching is minimized where possible by using region-of-interest capture for play-button detection and threshold-based early exits.

## Disclaimer

This project automates GUI interactions in a third-party desktop application. Behavior may change when the application UI, theme, or workflow is updated.
