import os
import re
import logging
import warnings
import cv2
import numpy as np
import easyocr

seen={}
warnings.filterwarnings("ignore")
logging.getLogger("easyocr").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

try:
    import torch
    USE_GPU = bool(torch.cuda.is_available())
except Exception:
    USE_GPU = False

reader = easyocr.Reader(['en'], gpu=USE_GPU, verbose=False)


def Get_ID(img):
    img = np.array(img)
    
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    if img is None:
        return None, None

    
    h, w = img.shape[:2]

    img = img[:, int(w * 0.32):]

    img = cv2.resize(
        img,
        None,
        fx=5,
        fy=5,
        interpolation=cv2.INTER_CUBIC
    )

    roi = img

   
    gray = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2GRAY
    )

    clahe = cv2.createCLAHE(
        clipLimit=3,
        tileGridSize=(8,8)
    )

    clahe_gray = clahe.apply(gray)

    

    kernel = np.array([
        [0,-1,0],
        [-1,5,-1],
        [0,-1,0]
    ])

    median = cv2.medianBlur(
        gray,
        5
    )

    bilateral = cv2.bilateralFilter(
        gray,
        9,
        75,
        75
    )

    erosion = cv2.erode(
        gray,
        np.ones((2,2), np.uint8),
        iterations=1
    )

    sharpen = cv2.filter2D(
        gray,
        -1,
        kernel
    )

    variants = {
        "gray": gray,
        "clahe": clahe_gray,
        "median": median,
        "bilateral": bilateral,
        "erosion": erosion,
        "sharpen": sharpen
    }

    # --------------------
    # OCR
    # --------------------

    max_conf = 0
    best_text = None

    h_gray = gray.shape[0]

    regions = {
        "top": (0, h_gray // 2),
        "middle": (h_gray // 2, 2 * h_gray // 2),
    }

    for region_name, (s, e) in regions.items():

   
        if max_conf >= 0.995:
            break

        for variant_name, image in variants.items():

        
            if max_conf >= 0.995:
                break

            crop = image[s:e, :]
          

            results = reader.readtext(
                crop,
                contrast_ths=0.05,
                adjust_contrast=0.8,
                text_threshold=0.5,
                low_text=0.2,
                link_threshold=0.3,
                detail=1,
                paragraph=False,
                allowlist="0123456789"
            )

            for bbox, text, conf in results:
                conf=float(conf)
                text = text.strip()

                m = re.search(r"\d{10,}", text)

                if not m:
                    continue

                number = m.group()

                if conf > max_conf:
                    max_conf = conf
                    best_text = number
    if best_text in seen and seen[best_text] > max_conf:
        return None, None
    seen[best_text] = max_conf
    return best_text, max_conf