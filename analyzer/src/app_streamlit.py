# src/app_streamlit.py

import os
import tempfile

import streamlit as st
from PIL import Image

from predict_final import predict_final


# =====================================================
# Page config
# =====================================================

st.set_page_config(
    page_title="Color Analysis AI",
    page_icon="🎨",
    layout="centered"
)


# =====================================================
# Constants
# =====================================================

MODEL_PATH = "models/convnext_tiny_multi_output.pth"
UPLOAD_DIR = "temp_uploads"

# Konfigurasi preprocessing untuk Streamlit
# Untuk foto user asli:
# - use_white_balance=False mengikuti hasil testing terakhir
# - use_face_crop=True agar wajah user lebih fokus dianalisis
USE_WHITE_BALANCE = False
USE_FACE_CROP = True

os.makedirs(UPLOAD_DIR, exist_ok=True)


# =====================================================
# Helper functions
# =====================================================

def save_uploaded_file(uploaded_file):
    """
    Menyimpan file upload sementara agar bisa diproses oleh predict_final.py.
    """

    file_extension = os.path.splitext(uploaded_file.name)[1].lower()

    if file_extension not in [".jpg", ".jpeg", ".png", ".webp"]:
        file_extension = ".png"

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=file_extension,
        dir=UPLOAD_DIR
    )

    temp_file.write(uploaded_file.getbuffer())
    temp_file.close()

    return temp_file.name


def show_result_card(title, value):
    """
    Menampilkan hasil akhir dalam bentuk card.
    """

    st.markdown(
        f"""
        <div style="
            padding: 18px;
            border-radius: 16px;
            background-color: #ffffff;
            border: 1px solid #eeeeee;
            box-shadow: 0 4px 14px rgba(0,0,0,0.06);
            margin-bottom: 12px;
        ">
            <p style="
                margin: 0;
                font-size: 14px;
                color: #777777;
                font-weight: 500;
            ">{title}</p>
            <p style="
                margin: 6px 0 0 0;
                font-size: 24px;
                color: #222222;
                font-weight: 700;
            ">{value}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def format_value(value):
    """
    Merapikan format teks output.

    Contoh:
    - deep winter -> Deep Winter
    - neutral-cool -> Neutral Cool
    """

    if not isinstance(value, str):
        return value

    value = value.replace("-", " ")
    value = value.replace("_", " ")

    return value.title()


def safe_get(dictionary, key, default="-"):
    """
    Mengambil value dari dictionary dengan aman.
    """

    if not isinstance(dictionary, dict):
        return default

    return dictionary.get(key, default)


def format_confidence(value):
    """
    Merapikan nilai confidence agar aman ditampilkan.
    """

    if value is None:
        return "-"

    try:
        return f"{float(value):.4f}"
    except Exception:
        return str(value)


def format_score(value):
    """
    Merapikan nilai skor CV seperti brightness dan contrast score.
    """

    if value is None:
        return "-"

    try:
        return f"{float(value):.2f}"
    except Exception:
        return str(value)


# =====================================================
# UI Header
# =====================================================

st.title("🎨 Color Analysis AI")

st.write(
    "Upload foto wajah untuk mendapatkan hasil analisis warna berdasarkan "
    "kombinasi Machine Learning dan Computer Vision."
)

st.info(
    "Sistem akan menampilkan Color Type, Undertone, Skin Tone, dan Contrast. "
    "Hasil ini masih berupa baseline prediction, sehingga sebaiknya digunakan "
    "sebagai rekomendasi awal."
)


# =====================================================
# Model check
# =====================================================

if not os.path.exists(MODEL_PATH):
    st.error(
        f"Model tidak ditemukan di `{MODEL_PATH}`. "
        "Pastikan file `convnext_tiny_multi_output.pth` sudah ada di folder `models`."
    )
    st.stop()


# =====================================================
# Upload image
# =====================================================

uploaded_file = st.file_uploader(
    "Upload foto wajah",
    type=["jpg", "jpeg", "png", "webp"]
)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")

    st.markdown("### Preview Image")
    st.image(
        image,
        caption="Uploaded Image",
        use_container_width=True
    )

    analyze_button = st.button(
        "Analyze Color",
        type="primary",
        use_container_width=True
    )

    if analyze_button:
        image_path = None

        with st.spinner("Analyzing image..."):
            try:
                image_path = save_uploaded_file(uploaded_file)

                # =====================================================
                # Prediction
                # =====================================================
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

                st.success("Analysis complete!")

                # =====================================================
                # Final result
                # =====================================================

                st.markdown("## Result")

                show_result_card(
                    "Color Type",
                    format_value(safe_get(final_output, "color_type"))
                )

                show_result_card(
                    "Undertone",
                    format_value(safe_get(final_output, "undertone"))
                )

                show_result_card(
                    "Skin Tone",
                    format_value(safe_get(final_output, "skin_tone"))
                )

                show_result_card(
                    "Contrast",
                    format_value(safe_get(final_output, "contrast"))
                )

                st.warning(
                    "Hasil ini merupakan baseline prediction. "
                    "Akurasi model masih terbatas, sehingga hasil sebaiknya dianggap "
                    "sebagai rekomendasi awal, bukan hasil final mutlak."
                )

                # =====================================================
                # Technical details
                # =====================================================

                with st.expander("Show technical details"):
                    ml_prediction = result.get("ml_prediction", {})
                    cv_analysis = result.get("cv_analysis", {})
                    corrected_prediction = result.get("corrected_prediction", {})

                    st.markdown("### Preprocessing Configuration")
                    st.write(f"White Balance: `{USE_WHITE_BALANCE}`")
                    st.write(f"Face Crop: `{USE_FACE_CROP}`")

                    st.markdown("### ML Prediction")

                    season_prediction = safe_get(
                        ml_prediction,
                        "season_prediction"
                    )

                    subclass_prediction = safe_get(
                        ml_prediction,
                        "subclass_prediction"
                    )

                    season_confidence = safe_get(
                        ml_prediction,
                        "season_confidence",
                        None
                    )

                    subclass_confidence = safe_get(
                        ml_prediction,
                        "sub_class_confidence",
                        None
                    )

                    if subclass_confidence is None:
                        subclass_confidence = safe_get(
                            ml_prediction,
                            "subclass_confidence",
                            None
                        )

                    st.write(f"Season Prediction: `{season_prediction}`")
                    st.write(f"Subclass Prediction: `{subclass_prediction}`")
                    st.write(
                        f"Season Confidence: `{format_confidence(season_confidence)}`"
                    )
                    st.write(
                        f"Subclass Confidence: `{format_confidence(subclass_confidence)}`"
                    )

                    st.markdown("### Corrected Prediction")
                    st.json(corrected_prediction)

                    st.markdown("### Top Season Predictions")
                    st.json(
                        ml_prediction.get("season_top_k", [])
                    )

                    st.markdown("### Top Subclass Predictions")
                    st.json(
                        ml_prediction.get("subclass_top_k", [])
                    )

                    st.markdown("### CV Analysis")

                    brightness = cv_analysis.get("brightness", None)
                    contrast_score = cv_analysis.get("contrast_score", None)
                    rgb_tendency = cv_analysis.get("rgb_tendency", "-")
                    num_pixels_used = cv_analysis.get("num_pixels_used", "-")

                    st.write(f"Brightness: `{format_score(brightness)}`")
                    st.write(f"Contrast Score: `{format_score(contrast_score)}`")
                    st.write(f"RGB Tendency: `{rgb_tendency}`")
                    st.write(f"Pixels Used: `{num_pixels_used}`")

                    st.json(cv_analysis)

            except TypeError as e:
                st.error(
                    "Terjadi error pada parameter `predict_final()`. "
                    "Pastikan fungsi `predict_final` di `src/predict_final.py` "
                    "sudah menerima parameter `use_white_balance` dan `use_face_crop`."
                )
                st.code(str(e))

            except Exception as e:
                st.error(f"Terjadi error saat analisis: {e}")

            finally:
                if image_path is not None and os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                    except Exception:
                        pass

else:
    st.markdown("### Cara menggunakan")
    st.write(
        "1. Upload foto wajah.\n"
        "2. Klik tombol Analyze Color.\n"
        "3. Sistem akan menampilkan Color Type, Undertone, Skin Tone, dan Contrast."
    )


# =====================================================
# Footer
# =====================================================

st.markdown("---")
st.caption("Color Analysis AI · Hybrid Machine Learning + Computer Vision")