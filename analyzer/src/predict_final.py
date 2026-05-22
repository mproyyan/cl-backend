import os
import json
import argparse

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms, models

from cv_analyzer import analyze_image


def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    else:
        return torch.device("cpu")


class ConvNeXtTinyMultiOutput(nn.Module):
    def __init__(
        self,
        num_season_classes=4,
        num_subclass_classes=6,
        pretrained=False,
        dropout=0.4
    ):
        super().__init__()

        weights = models.ConvNeXt_Tiny_Weights.DEFAULT if pretrained else None
        base_model = models.convnext_tiny(weights=weights)

        self.features = base_model.features
        self.avgpool = base_model.avgpool

        in_features = base_model.classifier[2].in_features

        self.flatten = nn.Flatten(1)
        self.shared_dropout = nn.Dropout(p=dropout)

        self.season_head = nn.Linear(in_features, num_season_classes)
        self.subclass_head = nn.Linear(in_features, num_subclass_classes)

    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = self.flatten(x)
        x = self.shared_dropout(x)

        season_output = self.season_head(x)
        subclass_output = self.subclass_head(x)

        return season_output, subclass_output



def gray_world_white_balance(image, strength=0.6):
    image_np = np.asarray(image).astype(np.float32)

    mean_r = image_np[:, :, 0].mean()
    mean_g = image_np[:, :, 1].mean()
    mean_b = image_np[:, :, 2].mean()

    gray_mean = (mean_r + mean_g + mean_b) / 3.0

    scale_r = gray_mean / (mean_r + 1e-6)
    scale_g = gray_mean / (mean_g + 1e-6)
    scale_b = gray_mean / (mean_b + 1e-6)

    balanced_np = image_np.copy()
    balanced_np[:, :, 0] *= scale_r
    balanced_np[:, :, 1] *= scale_g
    balanced_np[:, :, 2] *= scale_b

    balanced_np = np.clip(balanced_np, 0, 255)

    final_np = (image_np * (1.0 - strength)) + (balanced_np * strength)
    final_np = np.clip(final_np, 0, 255).astype(np.uint8)

    return Image.fromarray(final_np)


def auto_face_center_crop(image):
    width, height = image.size

    if height > width * 1.2:
        crop_width = int(width * 0.92)
        crop_height = int(height * 0.68)

        left = int((width - crop_width) / 2)
        top = int(height * 0.12)

        right = left + crop_width
        bottom = top + crop_height

    else:
        crop_width = int(width * 0.75)
        crop_height = int(height * 0.75)

        left = int((width - crop_width) / 2)
        top = int((height - crop_height) / 2)

        right = left + crop_width
        bottom = top + crop_height

    left = max(0, left)
    top = max(0, top)
    right = min(width, right)
    bottom = min(height, bottom)

    return image.crop((left, top, right, bottom))


def preprocess_input_image(
    image_path,
    save_preprocessed_path="results/preprocessed_input.jpg",
    use_white_balance=True,
    use_face_crop=True
):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image tidak ditemukan: {image_path}")

    image = Image.open(image_path).convert("RGB")

    if use_face_crop:
        image = auto_face_center_crop(image)

    if use_white_balance:
        image = gray_world_white_balance(image, strength=0.6)

    if save_preprocessed_path is not None:
        save_dir = os.path.dirname(save_preprocessed_path)

        if save_dir != "":
            os.makedirs(save_dir, exist_ok=True)

        image.save(save_preprocessed_path)

    return image, save_preprocessed_path


def get_inference_transform():
    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])


def label_map_to_class_names(label_map):
    return [
        name for name, _ in sorted(
            label_map.items(),
            key=lambda item: item[1]
        )
    ]


def translate_season(season):
    season_translation = {
        "primavera": "spring",
        "estate": "summer",
        "autunno": "autumn",
        "inverno": "winter"
    }

    return season_translation.get(season, season)



def load_multi_output_model(model_path, device):
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model tidak ditemukan: {model_path}")

    checkpoint = torch.load(model_path, map_location=device)

    season_label_map = checkpoint["season_label_map"]
    subclass_label_map = checkpoint["subclass_label_map"]

    season_class_names = checkpoint.get(
        "season_class_names",
        label_map_to_class_names(season_label_map)
    )

    subclass_class_names = checkpoint.get(
        "subclass_class_names",
        label_map_to_class_names(subclass_label_map)
    )

    model = ConvNeXtTinyMultiOutput(
        num_season_classes=len(season_class_names),
        num_subclass_classes=len(subclass_class_names),
        pretrained=False,
        dropout=0.4
    )

    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    return model, season_class_names, subclass_class_names, checkpoint


# =====================================================
# ML prediction
# =====================================================

@torch.no_grad()
def predict_ml_from_image(
    image,
    model,
    season_class_names,
    subclass_class_names,
    device,
    top_k=3
):
    transform = get_inference_transform()
    image_tensor = transform(image).unsqueeze(0).to(device)

    season_logits, subclass_logits = model(image_tensor)

    season_probs = F.softmax(season_logits, dim=1)[0]
    subclass_probs = F.softmax(subclass_logits, dim=1)[0]

    season_confidence, season_index = torch.max(season_probs, dim=0)
    subclass_confidence, subclass_index = torch.max(subclass_probs, dim=0)

    season_prediction = season_class_names[season_index.item()]
    subclass_prediction = subclass_class_names[subclass_index.item()]

    season_top_values, season_top_indices = torch.topk(
        season_probs,
        k=min(top_k, len(season_class_names))
    )

    subclass_top_values, subclass_top_indices = torch.topk(
        subclass_probs,
        k=min(top_k, len(subclass_class_names))
    )

    season_top_k = []
    for value, index in zip(season_top_values, season_top_indices):
        label = season_class_names[index.item()]
        season_top_k.append({
            "label": label,
            "label_en": translate_season(label),
            "confidence": float(value.item())
        })

    subclass_top_k = []
    for value, index in zip(subclass_top_values, subclass_top_indices):
        label = subclass_class_names[index.item()]
        subclass_top_k.append({
            "label": label,
            "confidence": float(value.item())
        })

    return {
        "season": season_prediction,
        "season_en": translate_season(season_prediction),
        "season_confidence": float(season_confidence.item()),
        "sub_class": subclass_prediction,
        "sub_class_confidence": float(subclass_confidence.item()),
        "season_top_k": season_top_k,
        "subclass_top_k": subclass_top_k
    }



def estimate_undertone(season, sub_class, rgb_tendency=None):
    if sub_class == "warm":
        return "warm"

    if sub_class == "cool":
        return "cool"

    warm_seasons = ["primavera", "autunno"]
    cool_seasons = ["estate", "inverno"]

    if season in warm_seasons:
        return "warm"

    if season in cool_seasons:
        return "cool"

    if isinstance(rgb_tendency, str):
        rgb_tendency_lower = rgb_tendency.lower()

        if "warm" in rgb_tendency_lower:
            return "warm"

        if "cool" in rgb_tendency_lower:
            return "cool"

    return "warm"


def estimate_cv_undertone(cv_result):
    rgb_tendency = cv_result.get("rgb_tendency", None)

    if isinstance(rgb_tendency, str):
        rgb_tendency_lower = rgb_tendency.lower()

        if "warm" in rgb_tendency_lower:
            return "warm"

        if "cool" in rgb_tendency_lower:
            return "cool"

    mean_rgb = cv_result.get("mean_rgb", {})

    r = mean_rgb.get("r", None)
    b = mean_rgb.get("b", None)

    if r is not None and b is not None:
        if r >= b:
            return "warm"
        else:
            return "cool"

    return None


def build_color_type(season, sub_class):
    color_type_map = {
        ("primavera", "light"): "Light Spring",
        ("primavera", "warm"): "Warm Spring",
        ("primavera", "bright"): "Clear Spring",

        ("estate", "light"): "Light Summer",
        ("estate", "cool"): "Cool Summer",
        ("estate", "soft"): "Soft Summer",

        ("autunno", "soft"): "Soft Autumn",
        ("autunno", "warm"): "Warm Autumn",
        ("autunno", "deep"): "Deep Autumn",

        ("inverno", "deep"): "Deep Winter",
        ("inverno", "cool"): "Cool Winter",
        ("inverno", "bright"): "Clear Winter"
    }

    if (season, sub_class) in color_type_map:
        return color_type_map[(season, sub_class)]

    fallback_map = {
        "primavera": "Warm Spring",
        "estate": "Cool Summer",
        "autunno": "Warm Autumn",
        "inverno": "Deep Winter"
    }

    return fallback_map.get(season, "Unknown")


def estimate_contrast_from_subclass(sub_class):
    if sub_class in ["deep", "bright"]:
        return "high"

    if sub_class in ["soft", "light"]:
        return "low"

    return "medium"


def combine_contrast(cv_contrast, sub_class, contrast_score=None):
    subclass_hint = estimate_contrast_from_subclass(sub_class)

    if subclass_hint == "high":
        return "high"

    if subclass_hint == "low":
        return "low"

    if cv_contrast == "high":
        return "high"

    if cv_contrast == "low":
        return "low"

    if contrast_score is not None:
        if contrast_score >= 40:
            return "high"
        else:
            return "low"

    return "low"


def correct_season_with_cv(
    season,
    sub_class,
    season_confidence,
    sub_class_confidence,
    final_undertone,
    cv_undertone,
    final_contrast,
    cv_result
):
    corrected_season = season
    corrected_subclass = sub_class
    correction_reason = "no correction"

    contrast_score = cv_result.get("contrast_score", 0)
    brightness = cv_result.get("brightness", 0)
    skin_tone = cv_result.get("skin_tone", "")

    very_confident = season_confidence >= 0.80 and sub_class_confidence >= 0.65

    if very_confident:
        return corrected_season, corrected_subclass, correction_reason



    if (
        cv_undertone == "warm"
        and (skin_tone == "light" or brightness >= 145)
        and season_confidence < 0.60
    ):
        corrected_season = "autunno"
        corrected_subclass = "warm"

        correction_reason = (
            "light/bright warm face corrected to Warm Autumn before winter rule"
        )

        return corrected_season, corrected_subclass, correction_reason


    if season == "inverno" and cv_undertone == "warm":
        if skin_tone == "light" or brightness >= 145:
            corrected_season = "autunno"
            corrected_subclass = "warm"

            correction_reason = (
                "winter corrected to Warm Autumn because face is light/bright and warm"
            )

            return corrected_season, corrected_subclass, correction_reason

        if (
            sub_class == "deep"
            and final_contrast == "high"
            and brightness < 145
            and skin_tone in ["medium", "dark"]
        ):
            corrected_season = "inverno"
            corrected_subclass = "deep"

            correction_reason = (
                "winter deep prediction kept because darker face and high contrast support deep winter"
            )

            return corrected_season, corrected_subclass, correction_reason

        if (
            season_confidence < 0.45
            and sub_class not in ["cool", "deep"]
        ):
            corrected_season = "autunno"

            if final_contrast == "high" or contrast_score >= 45:
                corrected_subclass = "deep"
            else:
                corrected_subclass = "warm"

            correction_reason = (
                "winter predicted by ML, but low confidence and warm CV signal corrected to autumn"
            )

            return corrected_season, corrected_subclass, correction_reason

        return corrected_season, corrected_subclass, correction_reason



    if season == "estate" and cv_undertone == "warm":
        if season_confidence < 0.45:
            if final_contrast == "high" and brightness < 145:
                corrected_season = "autunno"
                corrected_subclass = "warm"
            else:
                corrected_season = "primavera"
                corrected_subclass = "warm"

            correction_reason = (
                "summer predicted by ML, but low confidence and warm CV signal corrected"
            )

            return corrected_season, corrected_subclass, correction_reason


    if season == "autunno" and sub_class == "deep":
        # Jika wajah light/bright, jangan geser ke Winter.
        # Lebih aman diarahkan ke Warm Autumn.
        if skin_tone == "light" or brightness >= 145:
            corrected_season = "autunno"
            corrected_subclass = "warm"

            correction_reason = (
                "autumn deep prediction adjusted to Warm Autumn because skin tone is light/bright and warm"
            )

            return corrected_season, corrected_subclass, correction_reason

        if (
            final_contrast == "high"
            and skin_tone in ["medium", "dark"]
            and brightness < 125
            and sub_class_confidence >= 0.65
        ):
            corrected_season = "inverno"
            corrected_subclass = "deep"

            correction_reason = (
                "autumn deep corrected to deep winter because medium/dark skin tone, "
                "low brightness, high final contrast, and strong deep subclass confidence"
            )

            return corrected_season, corrected_subclass, correction_reason

        if (
            final_contrast == "high"
            and contrast_score >= 44
            and season_confidence < 0.45
            and brightness < 145
            and skin_tone in ["medium", "dark"]
        ):
            corrected_season = "inverno"
            corrected_subclass = "deep"

            correction_reason = (
                "autumn deep predicted by ML, but medium/dark skin tone, low brightness, "
                "low confidence, and high contrast suggest deep winter"
            )

            return corrected_season, corrected_subclass, correction_reason



    if season == "autunno" and cv_undertone == "cool":
        if (
            final_contrast == "high"
            and contrast_score >= 45
            and season_confidence < 0.55
            and brightness < 145
            and skin_tone in ["medium", "dark"]
        ):
            corrected_season = "inverno"
            corrected_subclass = "deep"

            correction_reason = (
                "autumn predicted by ML, but cool CV signal, medium/dark skin tone, "
                "and high contrast suggest deep winter"
            )

            return corrected_season, corrected_subclass, correction_reason



    if season == "primavera" and cv_undertone == "cool":
        if season_confidence < 0.45:
            corrected_season = "estate"

            if sub_class == "light":
                corrected_subclass = "light"
            else:
                corrected_subclass = "cool"

            correction_reason = (
                "spring predicted by ML, but low confidence and cool CV signal corrected to summer"
            )

            return corrected_season, corrected_subclass, correction_reason

    return corrected_season, corrected_subclass, correction_reason



def predict_final(
    image_path,
    model_path="models/convnext_tiny_multi_output.pth",
    mask_path=None,
    save_json_path=None,
    save_preprocessed_path="results/preprocessed_input.jpg",
    top_k=3,
    use_white_balance=True,
    use_face_crop=True
):
    device = get_device()

    model, season_class_names, subclass_class_names, checkpoint = load_multi_output_model(
        model_path=model_path,
        device=device
    )

    preprocessed_image, preprocessed_image_path = preprocess_input_image(
        image_path=image_path,
        save_preprocessed_path=save_preprocessed_path,
        use_white_balance=use_white_balance,
        use_face_crop=use_face_crop
    )

    ml_result = predict_ml_from_image(
        image=preprocessed_image,
        model=model,
        season_class_names=season_class_names,
        subclass_class_names=subclass_class_names,
        device=device,
        top_k=top_k
    )

    cv_result = analyze_image(
        image_path=preprocessed_image_path,
        mask_path=mask_path,
        save_json_path=None,
        use_center_crop=True,
        crop_ratio=0.62
    )

    season_prediction = ml_result["season"]
    subclass_prediction = ml_result["sub_class"]

    subclass_contrast_hint = estimate_contrast_from_subclass(
        subclass_prediction
    )

    final_contrast = combine_contrast(
        cv_contrast=cv_result["contrast"],
        sub_class=subclass_prediction,
        contrast_score=cv_result.get("contrast_score")
    )

    ml_undertone = estimate_undertone(
        season=season_prediction,
        sub_class=subclass_prediction,
        rgb_tendency=cv_result.get("rgb_tendency")
    )

    cv_undertone = estimate_cv_undertone(cv_result)

    corrected_season, corrected_subclass, correction_reason = correct_season_with_cv(
        season=season_prediction,
        sub_class=subclass_prediction,
        season_confidence=ml_result["season_confidence"],
        sub_class_confidence=ml_result["sub_class_confidence"],
        final_undertone=ml_undertone,
        cv_undertone=cv_undertone,
        final_contrast=final_contrast,
        cv_result=cv_result
    )

    final_undertone = estimate_undertone(
        season=corrected_season,
        sub_class=corrected_subclass,
        rgb_tendency=cv_result.get("rgb_tendency")
    )

    color_type = build_color_type(
        season=corrected_season,
        sub_class=corrected_subclass
    )

    final_result = {
        "image_path": image_path,
        "preprocessed_image_path": preprocessed_image_path,
        "mask_path": mask_path,
        "model_path": model_path,
        "device": str(device),

        "final_output": {
            "undertone": final_undertone,
            "skin_tone": cv_result["skin_tone"],
            "contrast": final_contrast,
            "color_type": color_type
        },

        "ml_prediction": {
            "season": ml_result["season"],
            "season_en": ml_result["season_en"],
            "season_confidence": ml_result["season_confidence"],
            "sub_class": ml_result["sub_class"],
            "sub_class_confidence": ml_result["sub_class_confidence"],
            "season_top_k": ml_result["season_top_k"],
            "subclass_top_k": ml_result["subclass_top_k"]
        },

        "corrected_prediction": {
            "original_season": ml_result["season"],
            "original_season_en": ml_result["season_en"],
            "original_sub_class": ml_result["sub_class"],
            "corrected_season": corrected_season,
            "corrected_season_en": translate_season(corrected_season),
            "corrected_sub_class": corrected_subclass,
            "is_corrected": (
                corrected_season != ml_result["season"]
                or corrected_subclass != ml_result["sub_class"]
            ),
            "correction_reason": correction_reason
        },

        "cv_analysis": cv_result,

        "preprocessing": {
            "use_white_balance": use_white_balance,
            "use_face_crop": use_face_crop,
            "white_balance_method": "gray_world_blended_strength_0.6",
            "crop_method": "simple_portrait_upper_center_crop"
        },

        "interpretation_notes": {
            "undertone_source": "estimated from corrected ML season/subclass with warm or cool final categories",
            "skin_tone_source": "computer vision brightness from filtered skin-like pixels after preprocessing",
            "contrast_source": "binary low/high contrast combined from computer vision contrast score and ML subclass hint",
            "cv_undertone": cv_undertone,
            "ml_undertone_before_correction": ml_undertone,
            "cv_contrast": cv_result["contrast"],
            "subclass_contrast_hint": subclass_contrast_hint,
            "correction_source": "post-processing correction using ML prediction, confidence, CV undertone, brightness, skin tone, and CV contrast",
            "warning": "This is a baseline prediction. ML accuracy is still limited, so results should be treated as recommendation, not absolute truth."
        }
    }

    if save_json_path is not None:
        save_dir = os.path.dirname(save_json_path)

        if save_dir != "":
            os.makedirs(save_dir, exist_ok=True)

        with open(save_json_path, "w", encoding="utf-8") as f:
            json.dump(final_result, f, indent=4)

    return final_result



def main():
    parser = argparse.ArgumentParser(
        description="Final prediction: ML season/subclass + CV skin tone/contrast"
    )

    parser.add_argument(
        "--image",
        type=str,
        required=True,
        help="Path ke gambar input"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="models/convnext_tiny_multi_output.pth",
        help="Path model multi-output"
    )

    parser.add_argument(
        "--mask",
        type=str,
        default=None,
        help="Path mask opsional"
    )

    parser.add_argument(
        "--save",
        type=str,
        default=None,
        help="Path output JSON opsional"
    )

    parser.add_argument(
        "--save-preprocessed",
        type=str,
        default="results/preprocessed_input.jpg",
        help="Path untuk menyimpan gambar hasil preprocessing"
    )

    parser.add_argument(
        "--no-white-balance",
        action="store_true",
        help="Matikan white balance"
    )

    parser.add_argument(
        "--no-face-crop",
        action="store_true",
        help="Matikan face crop sederhana"
    )

    args = parser.parse_args()

    result = predict_final(
        image_path=args.image,
        model_path=args.model,
        mask_path=args.mask,
        save_json_path=args.save,
        save_preprocessed_path=args.save_preprocessed,
        use_white_balance=not args.no_white_balance,
        use_face_crop=not args.no_face_crop
    )

    final_output = result["final_output"]
    ml = result["ml_prediction"]
    corrected = result["corrected_prediction"]
    cv = result["cv_analysis"]

    print("\n==============================")
    print("Final Color Analysis Result")
    print("==============================")
    print(f"Image Path       : {result['image_path']}")
    print(f"Preprocessed     : {result['preprocessed_image_path']}")
    print(f"Model Path       : {result['model_path']}")
    print(f"Device           : {result['device']}")

    print("\nFinal Output")
    print("------------------------------")
    print(f"Color Type       : {final_output['color_type']}")
    print(f"Undertone        : {final_output['undertone']}")
    print(f"Skin Tone        : {final_output['skin_tone']}")
    print(f"Contrast         : {final_output['contrast']}")

    print("\nML Prediction")
    print("------------------------------")
    print(f"Season           : {ml['season_en']} ({ml['season']})")
    print(f"Sub Class        : {ml['sub_class']}")
    print(f"Season Conf      : {ml['season_confidence']:.4f}")
    print(f"Sub Class Conf   : {ml['sub_class_confidence']:.4f}")

    print("\nCorrected Prediction")
    print("------------------------------")
    print(f"Original Season   : {corrected['original_season_en']} ({corrected['original_season']})")
    print(f"Original Subclass : {corrected['original_sub_class']}")
    print(f"Corrected Season  : {corrected['corrected_season_en']} ({corrected['corrected_season']})")
    print(f"Corrected Subclass: {corrected['corrected_sub_class']}")
    print(f"Is Corrected      : {corrected['is_corrected']}")
    print(f"Reason            : {corrected['correction_reason']}")

    print("\nCV Analysis")
    print("------------------------------")
    print(f"Mean RGB         : ({cv['mean_rgb']['r']:.2f}, {cv['mean_rgb']['g']:.2f}, {cv['mean_rgb']['b']:.2f})")
    print(f"Brightness       : {cv['brightness']:.2f}")
    print(f"Contrast Score   : {cv['contrast_score']:.2f}")
    print(f"RGB Tendency     : {cv['rgb_tendency']}")
    print(f"Pixels Used      : {cv['num_pixels_used']}")

    print("\nPreprocessing")
    print("------------------------------")
    print(f"White Balance    : {result['preprocessing']['use_white_balance']}")
    print(f"Face Crop        : {result['preprocessing']['use_face_crop']}")

    print("\nNote")
    print("------------------------------")
    print(result["interpretation_notes"]["warning"])


if __name__ == "__main__":
    main()