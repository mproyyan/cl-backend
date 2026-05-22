# api.py

import os
import sys
import tempfile

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware


# =====================================================
# Fix import path
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")

if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)


from predict_final import predict_final


# =====================================================
# App config
# =====================================================

app = FastAPI(
    title="Color Analysis AI API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================
# Constants
# =====================================================

MODEL_PATH = "models/convnext_tiny_multi_output.pth"

USE_WHITE_BALANCE = False
USE_FACE_CROP = True


# =====================================================
# Helper functions
# =====================================================

def normalize_value(value):
    if not isinstance(value, str):
        return value

    return value.replace("_", " ").replace("-", " ").lower()


def save_uploaded_file(file: UploadFile):
    filename = file.filename or "uploaded.jpg"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=ext
    )

    temp_file.write(file.file.read())
    temp_file.close()

    return temp_file.name


# =====================================================
# Routes
# =====================================================

@app.get("/")
def root():
    return {
        "message": "Color Analysis AI API is running",
        "docs": "/docs",
        "endpoint": "/api/v1/color-analysis"
    }


@app.get("/health")
def health():
    return {
        "service": "color-analysis-ai",
        "status": "ok"
    }


@app.post("/api/v1/color-analysis")
async def color_analysis(image: UploadFile = File(...)):
    if not os.path.exists(MODEL_PATH):
        raise HTTPException(
            status_code=500,
            detail=f"Model not found: {MODEL_PATH}"
        )

    if image.content_type not in [
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp"
    ]:
        raise HTTPException(
            status_code=400,
            detail="File must be an image: jpg, jpeg, png, or webp"
        )

    image_path = None

    try:
        image_path = save_uploaded_file(image)

        result = predict_final(
            image_path=image_path,
            model_path=MODEL_PATH,
            mask_path=None,
            save_json_path=None,
            top_k=3,
            use_white_balance=USE_WHITE_BALANCE,
            use_face_crop=USE_FACE_CROP
        )

        final_output = result.get("final_output", {})

        color_type = normalize_value(final_output.get("color_type", "-"))
        undertone = normalize_value(final_output.get("undertone", "-"))
        skin_tone = normalize_value(final_output.get("skin_tone", "-"))
        contrast = normalize_value(final_output.get("contrast", "-"))

        return {
            "success": True,
            "message": "Color analysis complete",
            "data": {
                "color_type": color_type,
                "undertone": undertone,
                "skintone": skin_tone,
                "skin_tone": skin_tone,
                "contrast": contrast
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if image_path is not None and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception:
                pass