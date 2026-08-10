import os
import time
import cv2
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image
from utilities.OCR_Worker import waiting,OCR_Worker
from utilities.OCR_Worker import _rows
import threading
VERBOSE_LOGS = False


def log(message):
    if VERBOSE_LOGS:
        print(message)

worker = threading.Thread(target=OCR_Worker,daemon=True)
worker.start()


SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(SCRIPT_DIR, "reports")
SCREENSHOTS_DIR = os.path.join(REPORTS_DIR, "screenshots")

FONT = Font(name="Segoe UI", size=11)
HEADER_FONT = Font(name="Segoe UI", bold=True, color="FFFFFF", size=11)
HEADER_FILL = PatternFill(start_color="1A73E8", end_color="1A73E8", fill_type="solid")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
BORDER = Border(
    left=Side(style="thin", color="CCCCCC"),
    right=Side(style="thin", color="CCCCCC"),
    top=Side(style="thin", color="CCCCCC"),
    bottom=Side(style="thin", color="CCCCCC"),
)
IMG_SCALE = 0.7
HEADERS = ["S.No", "CAMERA ID", "CONF", "SCREENSHOT", "RECORDING", "OPENED"]
COL_WIDTHS = [8, 18, 10, 60, 14, 14]

_counter = 0
_current = None
stop_event = threading.Event()


def _ensure():
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def save_card_screenshot(crop_bgr):
    global _counter, _current
    _ensure()
    _counter += 1
    fname = f"card_{_counter:04d}_{time.strftime('%Y%m%d_%H%M%S')}.png"
    cv2.imwrite(os.path.join(SCREENSHOTS_DIR, fname), crop_bgr)
    _current = {"screenshot": fname,"image":crop_bgr.copy()}
def end_cycle(recording, opened):
    global _current
    if not _current:
        return
    
    _current["recording"]=recording
    _current["opened"]=opened
    waiting.put(_current)
    _current = None


def _write(ws, row, col, value):
    cell = ws.cell(row=row, column=col, value=value)
    cell.font = FONT
    cell.alignment = CENTER
    cell.border = BORDER
    return cell


def save_report(timeout=None):
    deadline = None if timeout is None else time.time() + timeout
    while waiting.unfinished_tasks:
        if deadline is not None and time.time() >= deadline:
            break
        time.sleep(0.1)
    rows = list(_rows)
    if not rows:
        log("[REPORT] No rows to save")
        return
    _ensure()

    path = os.path.join(REPORTS_DIR, f"report_{time.strftime('%Y%m%d_%H%M%S')}.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "Camera Report"

    for col_idx, (h, w) in enumerate(zip(HEADERS, COL_WIDTHS), 1):
        cell = ws.cell(row=1, column=col_idx, value=h)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL
        cell.alignment = CENTER
        cell.border = BORDER
        ws.column_dimensions[get_column_letter(col_idx)].width = w
    ws.row_dimensions[1].height = 28

    for i, r in enumerate(rows):
        row = i + 2
        _write(ws, row, 1, i + 1)
        _write(ws, row, 2, r["id"])
        _write(ws, row, 3, r["conf"])

        img_path = os.path.join(SCREENSHOTS_DIR, r["screenshot"])
        if os.path.exists(img_path):
            img = Image(img_path)
            img.width = int(img.width * IMG_SCALE)
            img.height = int(img.height * IMG_SCALE)
            ws.add_image(img, f"D{row}")
            ws.row_dimensions[row].height = max(img.height + 8, 50)
        else:
            _write(ws, row, 4, "(file not found)")
            ws.row_dimensions[row].height = 50

        _write(ws, row, 5, r["recording"])
        _write(ws, row, 6, r["opened"])

    wb.save(path)
    log(f"[REPORT] Saved: {path}")
    log(f"[REPORT] Total cameras: {len(rows)}")
