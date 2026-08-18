import os
import threading
from queue import Queue
from utilities.OCR import Get_ID
from utilities.block_mapper import CameraLookup

waiting = Queue()
_rows = []
_current = None

Mapper_File_Path = None

_worker_started = False


def _set_mapper_file_path(mapper_path: str) -> None:
    global Mapper_File_Path
    Mapper_File_Path = mapper_path


def start_worker():
    global _worker_started
    if _worker_started:
        return
    _worker_started = True
    worker = threading.Thread(target=OCR_Worker, daemon=True)
    worker.start()


def OCR_Worker():

    camera_lookup = None

    if Mapper_File_Path and os.path.exists(Mapper_File_Path):
        camera_lookup = CameraLookup(Mapper_File_Path)
    else:
        print(
            "[OCR] Mapper Excel not found; "
            "block/gaushala will be empty"
        )

    while True:
        item = waiting.get()

        try:
            if not item:

                return

            crop_bgr = item["image"]

            screenshot = item["screenshot"]

            recording = item["recording"]

            opened = item["opened"]
            camera_id, conf = Get_ID(
                crop_bgr
            )

            if camera_id is None:

                print(
                    "[OCR] Camera ID not detected"
                )

                continue

            block = gaushala = None

            if camera_lookup is not None:
                block, gaushala = camera_lookup.get(
                    camera_id
                )

            _rows.append({

                "id": camera_id,

                "block": block,

                "gaushala": gaushala,

                "conf": conf,

                "screenshot": screenshot,

                "recording": (
                    "Yes"
                    if recording
                    else "No"
                ),

                "opened": (
                    "Yes"
                    if opened
                    else "No"
                ),

            })

        except Exception as e:

            print(
                f"[OCR WORKER ERROR] {e}"
            )
        finally:

            waiting.task_done()
