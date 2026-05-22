import os
import json
import argparse
import numpy as np
from PIL import Image


# =====================================================
# Image helper
# =====================================================

def load_rgb_image(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image tidak ditemukan: {image_path}")

    image = Image.open(image_path).convert("RGB")
    return np.array(image)


def load_mask(mask_path, target_size=None):
    if mask_path is None:
        return None

    if not os.path.exists(mask_path):
        raise FileNotFoundError(f"Mask tidak ditemukan: {mask_path}")

    mask = Image.open(mask_path).convert("L")

    if target_size is not None:
        mask = mask.resize(target_size, Image.NEAREST)

    mask = np.array(mask)
    return mask


# =====================================================
# Region selection
# =====================================================

def center_crop_array(image_rgb, crop_ratio=0.62):
    """
    Mengambil area tengah gambar agar rambut, tepi mask,
    dan background tidak terlalu dominan.

    crop_ratio 0.62 artinya mengambil sekitar 62% area tengah.
    """

    h, w = image_rgb.shape[:2]

    crop_h = int(h * crop_ratio)
    crop_w = int(w * crop_ratio)

    start_y = max((h - crop_h) // 2, 0)
    start_x = max((w - crop_w) // 2, 0)

    end_y = start_y + crop_h
    end_x = start_x + crop_w

    cropped = image_rgb[start_y:end_y, start_x:end_x]

    return cropped


def center_crop_mask(mask, crop_ratio=0.62):
    if mask is None:
        return None

    h, w = mask.shape[:2]

    crop_h = int(h * crop_ratio)
    crop_w = int(w * crop_ratio)

    start_y = max((h - crop_h) // 2, 0)
    start_x = max((w - crop_w) // 2, 0)

    end_y = start_y + crop_h
    end_x = start_x + crop_w

    cropped = mask[start_y:end_y, start_x:end_x]

    return cropped


# =====================================================
# Pixel extraction
# =====================================================

def get_pixels_from_mask(image_rgb, mask=None, min_mask_value=10):
    """
    Mengambil pixel valid dari area wajah.

    Jika mask tersedia:
    - pixel diambil dari area mask > min_mask_value

    Jika mask tidak tersedia:
    - pixel diambil dari area non-background.
    - background hitam pada RGB-M dibuang.
    """

    if mask is not None:
        if mask.shape[:2] != image_rgb.shape[:2]:
            raise ValueError("Ukuran mask dan image tidak sama")

        selected_pixels = image_rgb[mask > min_mask_value]
    else:
        brightness = image_rgb.mean(axis=2)
        selected_pixels = image_rgb[brightness > 25]

    if len(selected_pixels) == 0:
        raise ValueError("Tidak ada pixel valid yang bisa dianalisis")

    return selected_pixels


def filter_skin_like_pixels(pixels):
    """
    Filter sederhana untuk memilih pixel yang lebih mirip kulit.

    Tujuannya bukan segmentasi kulit sempurna, tapi mengurangi dominasi:
    - rambut sangat gelap
    - background
    - shadow ekstrem
    - highlight ekstrem
    - warna yang terlalu hijau/biru

    Filter dibuat longgar agar tetap aman untuk berbagai skin tone.
    """

    pixels = pixels.astype(np.float32)

    r = pixels[:, 0]
    g = pixels[:, 1]
    b = pixels[:, 2]

    brightness = (0.299 * r) + (0.587 * g) + (0.114 * b)

    # Buang pixel terlalu gelap/terang ekstrem.
    basic_mask = (brightness >= 45) & (brightness <= 230)

    # Kulit umumnya punya R cukup kuat dibanding B,
    # tapi dibuat longgar agar cool/olive skin tidak langsung hilang.
    color_mask = (
        (r > 45) &
        (g > 35) &
        (b > 25) &
        (r >= b - 10) &
        (r >= g - 35) &
        ((r - b) <= 95) &
        ((r - g) <= 80)
    )

    filtered = pixels[basic_mask & color_mask]

    # Kalau filter terlalu ketat, fallback ke outlier removal saja.
    if len(filtered) < max(500, len(pixels) * 0.08):
        return remove_outlier_pixels(pixels)

    return filtered


# =====================================================
# RGB / brightness statistics
# =====================================================

def remove_outlier_pixels(pixels, lower_percentile=10, upper_percentile=90):
    """
    Menghapus pixel ekstrem seperti highlight terlalu terang
    dan shadow terlalu gelap.
    """

    pixels = pixels.astype(np.float32)

    brightness = (
        0.299 * pixels[:, 0] +
        0.587 * pixels[:, 1] +
        0.114 * pixels[:, 2]
    )

    low = np.percentile(brightness, lower_percentile)
    high = np.percentile(brightness, upper_percentile)

    filtered_pixels = pixels[(brightness >= low) & (brightness <= high)]

    if len(filtered_pixels) == 0:
        return pixels

    return filtered_pixels


def calculate_mean_rgb(pixels):
    mean_rgb = pixels.mean(axis=0)
    return mean_rgb


def calculate_brightness(mean_rgb):
    """
    Menghitung luminance dari RGB.
    """

    r, g, b = mean_rgb
    brightness = (0.299 * r) + (0.587 * g) + (0.114 * b)
    return brightness


# =====================================================
# Skin tone classification
# =====================================================

def classify_skin_tone(brightness):
    """
    Klasifikasi skin tone baseline berbasis brightness.

    Threshold dibuat sedikit lebih rendah dibanding versi awal
    karena pixel yang dipakai sekarang lebih selektif.
    """

    if brightness >= 155:
        return "light"
    elif brightness >= 95:
        return "medium"
    else:
        return "dark"


# =====================================================
# Contrast calculation
# =====================================================

def calculate_contrast(pixels):
    """
    Menghitung contrast dari area kulit/wajah yang sudah difilter.

    Versi revisi:
    - tidak hanya memakai p90-p10 karena terlalu sensitif
    - memakai gabungan spread percentile dan standard deviation
    """

    pixels = pixels.astype(np.float32)

    brightness = (
        0.299 * pixels[:, 0] +
        0.587 * pixels[:, 1] +
        0.114 * pixels[:, 2]
    )

    p20 = np.percentile(brightness, 20)
    p80 = np.percentile(brightness, 80)
    spread = p80 - p20
    std = np.std(brightness)

    # Gabungan agar tidak terlalu agresif seperti p90-p10.
    contrast_score = (0.65 * spread) + (0.35 * std)

    return contrast_score, p20, p80, std


def classify_contrast(contrast_score):
    """
    Klasifikasi contrast baseline yang lebih konservatif.

    Output:
    - low
    - medium
    - high
    """

    if contrast_score >= 55:
        return "high"
    elif contrast_score >= 28:
        return "medium"
    else:
        return "low"


# =====================================================
# RGB tendency
# =====================================================

def estimate_rgb_tendency(mean_rgb):
    """
    Ini bukan undertone final.
    Ini hanya indikasi kecenderungan warna dari mean RGB.
    Undertone final tetap lebih baik digabung dari ML + CV.
    """

    r, g, b = mean_rgb

    red_blue_diff = r - b
    red_green_diff = r - g

    if red_blue_diff > 22 and red_green_diff > 8:
        return "warm_rgb_tendency"
    elif red_blue_diff < 8:
        return "cool_rgb_tendency"
    else:
        return "neutral_rgb_tendency"


# =====================================================
# Main analyzer
# =====================================================

def analyze_image(
    image_path,
    mask_path=None,
    save_json_path=None,
    use_center_crop=True,
    crop_ratio=0.62
):
    image_rgb = load_rgb_image(image_path)

    mask = None
    if mask_path is not None:
        mask = load_mask(mask_path, target_size=(image_rgb.shape[1], image_rgb.shape[0]))

    original_shape = image_rgb.shape

    if use_center_crop:
        image_rgb = center_crop_array(image_rgb, crop_ratio=crop_ratio)
        mask = center_crop_mask(mask, crop_ratio=crop_ratio)

    pixels = get_pixels_from_mask(image_rgb, mask=mask)

    # Tahap 1: buang outlier ekstrem.
    pixels_no_outlier = remove_outlier_pixels(pixels)

    # Tahap 2: pilih pixel yang lebih mirip kulit.
    skin_pixels = filter_skin_like_pixels(pixels_no_outlier)

    mean_rgb = calculate_mean_rgb(skin_pixels)
    brightness = calculate_brightness(mean_rgb)
    skin_tone = classify_skin_tone(brightness)

    contrast_score, p20, p80, std = calculate_contrast(skin_pixels)
    contrast = classify_contrast(contrast_score)

    rgb_tendency = estimate_rgb_tendency(mean_rgb)

    result = {
        "image_path": image_path,
        "mask_path": mask_path,
        "use_center_crop": use_center_crop,
        "crop_ratio": crop_ratio,
        "original_shape": {
            "height": int(original_shape[0]),
            "width": int(original_shape[1])
        },
        "mean_rgb": {
            "r": float(mean_rgb[0]),
            "g": float(mean_rgb[1]),
            "b": float(mean_rgb[2])
        },
        "brightness": float(brightness),
        "skin_tone": skin_tone,
        "contrast_score": float(contrast_score),
        "contrast_percentile_20": float(p20),
        "contrast_percentile_80": float(p80),
        "contrast_brightness_std": float(std),
        "contrast": contrast,
        "rgb_tendency": rgb_tendency,
        "num_pixels_initial": int(len(pixels)),
        "num_pixels_used": int(len(skin_pixels))
    }

    if save_json_path is not None:
        os.makedirs(os.path.dirname(save_json_path), exist_ok=True)
        with open(save_json_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)

    return result


# =====================================================
# CLI testing
# =====================================================

def main():
    parser = argparse.ArgumentParser(description="Computer Vision analyzer untuk skin tone dan contrast")
    parser.add_argument("--image", type=str, required=True, help="Path ke gambar RGB atau RGB-M")
    parser.add_argument("--mask", type=str, default=None, help="Path ke mask opsional")
    parser.add_argument("--save", type=str, default=None, help="Path output JSON opsional")
    parser.add_argument("--no-center-crop", action="store_true", help="Matikan center crop")
    parser.add_argument("--crop-ratio", type=float, default=0.62, help="Rasio center crop, default 0.62")

    args = parser.parse_args()

    result = analyze_image(
        image_path=args.image,
        mask_path=args.mask,
        save_json_path=args.save,
        use_center_crop=not args.no_center_crop,
        crop_ratio=args.crop_ratio
    )

    print("\n==============================")
    print("CV Analysis Result")
    print("==============================")
    print(f"Image Path      : {result['image_path']}")
    print(f"Mask Path       : {result['mask_path']}")
    print(f"Center Crop     : {result['use_center_crop']}")
    print(f"Crop Ratio      : {result['crop_ratio']}")
    print(f"Mean RGB        : ({result['mean_rgb']['r']:.2f}, {result['mean_rgb']['g']:.2f}, {result['mean_rgb']['b']:.2f})")
    print(f"Brightness      : {result['brightness']:.2f}")
    print(f"Skin Tone       : {result['skin_tone']}")
    print(f"Contrast Score  : {result['contrast_score']:.2f}")
    print(f"Contrast Std    : {result['contrast_brightness_std']:.2f}")
    print(f"Contrast        : {result['contrast']}")
    print(f"RGB Tendency    : {result['rgb_tendency']}")
    print(f"Initial Pixels  : {result['num_pixels_initial']}")
    print(f"Pixels Used     : {result['num_pixels_used']}")


if __name__ == "__main__":
    main()
