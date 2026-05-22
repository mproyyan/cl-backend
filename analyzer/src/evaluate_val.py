import torch
import numpy as np
import matplotlib.pyplot as plt

from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay

from dataset import create_dataloaders
from model import build_efficientnetv2_s, get_device


def main():
    device = get_device()
    print("Device:", device)

    train_loader, val_loader, test_loader, label_map = create_dataloaders(
        batch_size=16,
        val_size=0.2
    )

    checkpoint = torch.load(
        "models/efficientnetv2_s_season.pth",
        map_location=device
    )

    unfreeze_last_blocks = checkpoint.get("unfreeze_last_blocks", 6)

    model = build_efficientnetv2_s(
        num_classes=4,
        pretrained=False,
        freeze_backbone=True,
        unfreeze_last_blocks=unfreeze_last_blocks
    )

    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)
    model.eval()

    idx_to_label = {v: k for k, v in label_map.items()}

    y_true = []
    y_pred = []

    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)

            outputs = model(images)
            predictions = torch.argmax(outputs, dim=1).cpu().numpy()

            y_pred.extend(predictions)
            y_true.extend(labels.numpy())

    target_names = [idx_to_label[i] for i in range(len(idx_to_label))]

    print("\nClassification Report Validation:")
    print(classification_report(y_true, y_pred, target_names=target_names))

    cm = confusion_matrix(y_true, y_pred)

    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=target_names
    )

    disp.plot(cmap="Blues", xticks_rotation=45)
    plt.title("Validation Confusion Matrix")
    plt.tight_layout()
    plt.savefig("results/val_confusion_matrix.png", dpi=300)
    plt.show()

    print("\nConfusion matrix disimpan di:")
    print("results/val_confusion_matrix.png")


if __name__ == "__main__":
    main()