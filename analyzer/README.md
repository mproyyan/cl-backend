# 🎨 Color Analysis AI

Color Analysis AI is a hybrid Machine Learning (ML) and Computer Vision (CV) application designed to analyze human facial images and determine personal color characteristics. It accurately predicts your **Color Type** (e.g., Deep Winter, Light Spring), **Undertone**, **Skin Tone**, and **Contrast**.

## 🌟 Features

- **Hybrid Analysis Approach:** Combines a Deep Learning model (ConvNeXt Tiny Multi-Output) with Computer Vision techniques (brightness, contrast, and RGB tendency analysis) for more accurate and robust predictions.
- **FastAPI Backend:** A fast and modern RESTful API for seamless integration with other services.
- **Streamlit Web UI:** An interactive and user-friendly web interface for quick image testing and visualization.
- **Comprehensive Training Pipeline:** Includes scripts for training baseline, subclass-only, and full multi-output models.

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.8+
- PyTorch

### 2. Installation

Install the required dependencies from the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

*Note: If you plan to run the API, make sure to install FastAPI, Uvicorn, and Python-Multipart as well:*
```bash
pip install fastapi uvicorn python-multipart
```

### 3. Model Setup

The application expects the trained model weights to be located in the `models/` directory. Ensure you have the `convnext_tiny_multi_output.pth` file placed correctly:
```text
models/convnext_tiny_multi_output.pth
```

## 💻 Usage

### Running the Streamlit Web Interface

To launch the interactive web application, run:

```bash
streamlit run src/app_streamlit.py
```

The app will be available at `http://localhost:8501`. You can upload an image of a face, and it will display the predicted Color Type, Undertone, Skin Tone, Contrast, and additional technical details from the CV analysis.

### Running the FastAPI Service

To start the API server, run:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

The API will be accessible at `http://localhost:8000`. 
- **Health Check:** `GET /health`
- **Prediction Endpoint:** `POST /api/v1/color-analysis` (accepts an image file upload `image`)
- **API Documentation:** `http://localhost:8000/docs` (Swagger UI)

## 📂 Project Structure

```text
├── api.py                              # FastAPI application entry point
├── check_data.py                       # Data checking utility
├── requirements.txt                    # Python dependencies
├── models/                             # Model weights directory
│   └── convnext_tiny_multi_output.pth  # PyTorch model weights
└── src/
    ├── app_streamlit.py                # Streamlit web interface
    ├── predict_final.py                # Core prediction logic (ML + CV fusion)
    ├── cv_analyzer.py                  # Computer Vision analysis utilities
    ├── model.py                        # PyTorch ConvNeXt model architecture
    ├── dataset.py                      # Custom dataset loader for training
    ├── train_multi_output.py           # Training script for multi-output model
    ├── train_convnext_tiny_baseline.py # Baseline training script
    ├── train_subclass_only.py          # Subclass training script
    ├── evaluate_final.py               # Main evaluation script
    └── evaluate_val.py                 # Validation evaluation script
```

## 🧠 How It Works

1. **Preprocessing:** The uploaded image can optionally undergo White Balance correction and Face Cropping to focus the analysis on the most relevant features.
2. **Machine Learning Prediction:** The image is passed through a fine-tuned ConvNeXt Tiny model that outputs initial predictions for Season and Subclass, along with confidence scores.
3. **Computer Vision Analysis:** The image is analyzed for brightness, contrast score, and RGB tendencies.
4. **Correction & Fusion Logic:** The initial ML predictions are refined and cross-validated using the CV analysis results to produce the final, corrected characteristics for Color Type, Undertone, Skin Tone, and Contrast.
