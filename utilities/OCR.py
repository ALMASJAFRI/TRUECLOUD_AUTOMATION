import os
import re
import logging
import warnings
import cv2
import numpy as np

from rapidocr import RapidOCR
# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

seen = {}
warnings.filterwarnings("ignore")
logging.disable(logging.WARNING)
logging.getLogger("rapidocr").setLevel(logging.ERROR)
logging.getLogger("onnxruntime").setLevel(logging.ERROR)

#buildex
# ---------------------------------------------------------
# RapidOCR
# ---------------------------------------------------------

engine = RapidOCR(
    params={
        "EngineConfig.onnxruntime.intra_op_num_threads": 4,
        "EngineConfig.onnxruntime.inter_op_num_threads": 1,

        "Det.det_thresh": 0.2,
        "Det.box_thresh": 0.3,

        "Global.min_height": 30,
        "Global.width_height_ratio": 8,
    }
)


# ---------------------------------------------------------
# GET ID
# ---------------------------------------------------------

def Get_ID(img):

    img = np.array(img)

    if img is None:
        return None, None

    # -----------------------------------------------------
    # RGB -> BGR
    # -----------------------------------------------------

    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    h, w = img.shape[:2]

    # -----------------------------------------------------
    # Crop left side
    # -----------------------------------------------------

    img = img[:, int(w * 0.32):]

    # -----------------------------------------------------
    # Resize
    # -----------------------------------------------------

    img = cv2.resize(
        img,
        None,
        fx=4,
        fy=4,
        interpolation=cv2.INTER_CUBIC
    )

    roi = img

    # -----------------------------------------------------
    # Grayscale
    # -----------------------------------------------------

    gray = cv2.cvtColor(
        roi,
        cv2.COLOR_BGR2GRAY
    )

    # -----------------------------------------------------
    # CLAHE
    # -----------------------------------------------------

    clahe = cv2.createCLAHE(
        clipLimit=3,
        tileGridSize=(8, 8)
    )

    
    clahe_gray = clahe.apply(gray)
    
    # -----------------------------------------------------
    # Sharpen kernel
    # -----------------------------------------------------

    kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ])

    # -----------------------------------------------------
    # Median
    # -----------------------------------------------------

    median = cv2.medianBlur(
        gray,
        5
    )

    # -----------------------------------------------------
    # Bilateral
    # -----------------------------------------------------

    bilateral = cv2.bilateralFilter(
        gray,
        9,
        75,
        75
    )

    # -----------------------------------------------------
    # Erosion
    # -----------------------------------------------------

    erosion = cv2.erode(
        gray,
        np.ones((2, 2), np.uint8),
        iterations=1
    )

    # -----------------------------------------------------
    # Sharpen
    # -----------------------------------------------------

    sharpen = cv2.filter2D(
        gray,
        -1,
        kernel
    )
    # -----------------------------------------------------
    # Same variants as your EasyOCR pipeline
    # -----------------------------------------------------

    variants = {
        "clahe": clahe_gray,
        "sharpen":sharpen,
        "gray": gray,
        "median":median
    }

    # -----------------------------------------------------
    # OCR
    # -----------------------------------------------------

    max_conf = 0
    best_text = None

    h_gray = gray.shape[0]

    overlap_ratio = 0.20
    overlap = int(h_gray * overlap_ratio)

    regions = {
        "top": (0, h_gray // 2),
        "middle": (h_gray // 2 - overlap, h_gray),
    }
    # -----------------------------------------------------
    # Region loop
    # -----------------------------------------------------

    for region_name, (s, e) in regions.items():

        if max_conf >= 0.99:
            break

        for variant_name, image in variants.items():

            if max_conf >= 0.99:
                break

            crop = image[s:e, :]

            # -------------------------------------------------
            # RapidOCR
            # -------------------------------------------------

            result = engine(
                    crop,
                    use_det=False,
                    use_cls=False,
                    use_rec=True
                )

            if result is None:
                continue

            # -------------------------------------------------
            # RapidOCR result
            #
            # result.txts
            # result.scores
            # -------------------------------------------------

            texts = result.txts
            scores = result.scores

            if texts is None or scores is None:
                continue

            # -------------------------------------------------
            # Process OCR results
            # -------------------------------------------------

            for text, conf in zip(texts, scores):

                if not text:
                    continue

                text = str(text).strip()
                conf = float(conf)

                # -------------------------------------------------
                # Extract 10 or more consecutive digits
                # -------------------------------------------------

                m = re.search(
                    r"\d{10,}",
                    text
                )

                if not m:
                    continue

                number = m.group()

                # -------------------------------------------------
                # Keep highest confidence result
                # -------------------------------------------------

                if conf > max_conf:

                    max_conf = conf
                    best_text = number

    # ---------------------------------------------------------
    # Duplicate protection
    # ---------------------------------------------------------

    if best_text is not None:

        if best_text in seen and seen[best_text] > max_conf:
            return None, None

        seen[best_text] = max_conf

    # ---------------------------------------------------------
    # Return
    # ---------------------------------------------------------

    return best_text, max_conf