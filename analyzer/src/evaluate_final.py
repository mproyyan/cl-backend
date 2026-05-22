import os
import json
from collections import Counter

from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

from predict_final import predict_final


def get_true_labels_from_path(image_path):
    """
    Ambil label asli dari struktur folder dataset.

    Contoh path:
    data/raw/images/RGB-M/test/autunno/deep/15701.png

    Maka:
    season = autunno
    sub_class = deep
    """

    parts = image_path.split(os.sep)

    season = parts[-3]
    sub_class = parts[-2]

    return season, sub_class


def collect_test_images(test_dir):
    image_paths = []

    valid_ext = (".jpg", ".jpeg", ".png", ".webp")

    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.lower().endswith(valid_ext):
                image_paths.append(os.path.join(root, file))

    return sorted(image_paths)


def main():
    test_dir = "data/raw/images/RGB-M/test"
    model_path = "models/convnext_tiny_multi_output.pth"

    output_json = "results/final_evaluation_results.json"
    season_cm_path = "results/final_season_confusion_matrix.png"
    subclass_cm_path = "results/final_subclass_confusion_matrix.png"

    image_paths = collect_test_images(test_dir)

    print("Total test images:", len(image_paths))

    y_true_season = []
    y_pred_season = []

    y_true_subclass = []
    y_pred_subclass = []

    final_color_types = []
    refined_count = 0

    detailed_results = []

    for idx, image_path in enumerate(image_paths, start=1):
        print(f"[{idx}/{len(image_paths)}] Processing: {image_path}")

        true_season, true_subclass = get_true_labels_from_path(image_path)

        try:
            result = predict_final(
                image_path=image_path,
                model_path=model_path,
                save_json_path=None,
                save_preprocessed_path="results/preprocessed_eval_temp.jpg",
                use_white_balance=False,
                use_face_crop=False
            )

            ml = result["ml_prediction"]
            refined = result["refined_prediction"]
            final_output = result["final_output"]

            pred_season = refined["refined_season"]
            pred_subclass = ml["sub_class"]

            y_true_season.append(true_season)
            y_pred_season.append(pred_season)

            y_true_subclass.append(true_subclass)
            y_pred_subclass.append(pred_subclass)

            final_color_types.append(final_output["color_type"])

            if refined["is_refined"]:
                refined_count += 1

            detailed_results.append({
                "image_path": image_path,
                "true_season": true_season,
                "true_subclass": true_subclass,
                "ml_season": ml["season"],
                "refined_season": pred_season,
                "pred_subclass": pred_subclass,
                "season_confidence": ml["season_confidence"],
                "subclass_confidence": ml["sub_class_confidence"],
                "is_refined": refined["is_refined"],
                "final_output": final_output,
                "cv_analysis": result["cv_analysis"]
            })

        except Exception as e:
            print(f"Error processing {image_path}: {e}")

    os.makedirs("results", exist_ok=True)

    print("\n==============================")
    print("Season Classification Report")
    print("==============================")
    print(classification_report(y_true_season, y_pred_season))

    print("\n==============================")
    print("Subclass Classification Report")
    print("==============================")
    print(classification_report(y_true_subclass, y_pred_subclass))

    print("\n==============================")
    print("Refinement Summary")
    print("==============================")
    print(f"Total refined: {refined_count}")
    print(f"Total images  : {len(y_true_season)}")
    print(f"Refined ratio : {refined_count / len(y_true_season):.4f}")

    print("\n==============================")
    print("Final Color Type Counts")
    print("==============================")
    color_type_counts = Counter(final_color_types)

    for color_type, count in color_type_counts.most_common():
        print(f"{color_type}: {count}")

    # Season confusion matrix
    season_labels = sorted(list(set(y_true_season + y_pred_season)))
    season_cm = confusion_matrix(
        y_true_season,
        y_pred_season,
        labels=season_labels
    )

    season_disp = ConfusionMatrixDisplay(
        confusion_matrix=season_cm,
        display_labels=season_labels
    )

    season_disp.plot(cmap="Blues", xticks_rotation=45)
    plt.title("Final Pipeline Season Confusion Matrix")
    plt.tight_layout()
    plt.savefig(season_cm_path, dpi=300)
    plt.close()

    # Subclass confusion matrix
    subclass_labels = sorted(list(set(y_true_subclass + y_pred_subclass)))
    subclass_cm = confusion_matrix(
        y_true_subclass,
        y_pred_subclass,
        labels=subclass_labels
    )

    subclass_disp = ConfusionMatrixDisplay(
        confusion_matrix=subclass_cm,
        display_labels=subclass_labels
    )

    subclass_disp.plot(cmap="Blues", xticks_rotation=45)
    plt.title("Final Pipeline Subclass Confusion Matrix")
    plt.tight_layout()
    plt.savefig(subclass_cm_path, dpi=300)
    plt.close()

    evaluation_result = {
        "total_images": len(y_true_season),
        "refined_count": refined_count,
        "refined_ratio": refined_count / len(y_true_season),
        "final_color_type_counts": dict(color_type_counts),
        "detailed_results": detailed_results
    }

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(evaluation_result, f, indent=4)

    print("\nFile saved:")
    print(output_json)
    print(season_cm_path)
    print(subclass_cm_path)


if __name__ == "__main__":
    main()