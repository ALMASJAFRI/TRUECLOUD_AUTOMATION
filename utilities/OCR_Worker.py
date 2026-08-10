from queue import Queue
from utilities.OCR import Get_ID
waiting=Queue()
_rows = []
_current = None

def OCR_Worker():
    while True:
        item = waiting.get()
        try:
            if not item :
                return
            crop_bgr=item["image"]
            screenshot=item["screenshot"]
            recording=item["recording"]
            opened=item["opened"]
            id,conf=Get_ID(crop_bgr)
            if id is None:
                continue
            _rows.append({
                "id": id,
                "conf":conf,
                "screenshot": screenshot,
                "recording": "Yes" if recording else "No",
                "opened": "Yes" if opened else "No",
            })
        except Exception:
            pass
        finally:
            waiting.task_done()