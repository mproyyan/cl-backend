import os
import json
import random
import numpy as np
import pandas as pd

import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from torchvision import models

from dataset import create_dataloaders


# =====================================================
# Reproducibility
# =====================================================

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    torch.backends.cudnn.deterministic = False
    torch.backends.cudnn.benchmark = True


# =====================================================
# Device
# =====================================================

def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    else:
        return torch.device("cpu")


# =====================================================
# Model
# =====================================================

def build_convnext_tiny(num_classes, freeze_backbone=False):
    weights = models.ConvNeXt_Tiny_Weights.DEFAULT
    model = models.convnext_tiny(weights=weights)

    if freeze_backbone:
        for param in model.features.parameters():
            param.requires_grad = False

    in_features = model.classifier[2].in_features

    model.classifier[2] = nn.Linear(in_features, num_classes)

    return model


# =====================================================
# Train and validation loop
# =====================================================

def train_one_epoch(model, dataloader, criterion, optimizer, device):
    model.train()

    running_loss = 0.0
    all_labels = []
    all_preds = []

    progress_bar = tqdm(dataloader, desc="Training", leave=True)

    for images, labels in progress_bar:
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)

        preds = torch.argmax(outputs, dim=1)
        all_labels.extend(labels.detach().cpu().numpy())
        all_preds.extend(preds.detach().cpu().numpy())

        current_loss = running_loss / len(all_labels)
        current_acc = accuracy_score(all_labels, all_preds)
        progress_bar.set_postfix({
            "loss": f"{current_loss:.4f}",
            "acc": f"{current_acc:.4f}"
        })

        current_loss = running_loss / len(all_labels)
        current_acc = accuracy_score(all_labels, all_preds)
        progress_bar.set_postfix({
            "loss": f"{current_loss:.4f}",
            "acc": f"{current_acc:.4f}"
        })

    epoch_loss = running_loss / len(dataloader.dataset)
    epoch_acc = accuracy_score(all_labels, all_preds)

    return epoch_loss, epoch_acc


@torch.no_grad()
def evaluate(model, dataloader, criterion, device):
    model.eval()

    running_loss = 0.0
    all_labels = []
    all_preds = []

    progress_bar = tqdm(dataloader, desc="Validation", leave=True)

    for images, labels in progress_bar:
        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)

        running_loss += loss.item() * images.size(0)

        preds = torch.argmax(outputs, dim=1)
        all_labels.extend(labels.detach().cpu().numpy())
        all_preds.extend(preds.detach().cpu().numpy())

    epoch_loss = running_loss / len(dataloader.dataset)
    epoch_acc = accuracy_score(all_labels, all_preds)

    return epoch_loss, epoch_acc, all_labels, all_preds


# =====================================================
# Save helpers
# =====================================================

def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# =====================================================
# Main training
# =====================================================

def main():
    set_seed(42)

    # ===============================
    # Config
    # ===============================
    csv_path = "data/raw/annotations.csv"
    image_base_dir = "data/raw/images"

    batch_size = 16
    image_size = 224
    num_epochs = 20
    learning_rate = 1e-4
    weight_decay = 1e-4
    val_size = 0.2
    num_workers = 0
    freeze_backbone = False

    save_dir = "results/convnext_tiny_baseline"
    model_save_path = "models/convnext_tiny_baseline.pth"

    os.makedirs(save_dir, exist_ok=True)
    os.makedirs("models", exist_ok=True)

    device = get_device()
    print(f"Using device: {device}")

    # ===============================
    # DataLoader
    # ===============================
    dataloader_result = create_dataloaders(
        csv_path=csv_path,
        image_base_dir=image_base_dir,
        batch_size=batch_size,
        val_size=val_size
    )

    # Support dua kemungkinan output dari dataset.py:
    # 1. train_loader, val_loader, test_loader, label_map
    # 2. train_loader, val_loader, test_loader, label_map, class_names
    if len(dataloader_result) == 4:
        train_loader, val_loader, test_loader, label_map = dataloader_result
        class_names = [name for name, _ in sorted(label_map.items(), key=lambda item: item[1])]
    else:
        train_loader, val_loader, test_loader, label_map, class_names = dataloader_result

    num_classes = len(class_names)

    print("Class names:", class_names)
    print("Label map:", label_map)
    print("Train samples:", len(train_loader.dataset))
    print("Val samples:", len(val_loader.dataset))
    print("Test samples:", len(test_loader.dataset))

    # ===============================
    # Model
    # ===============================
    model = build_convnext_tiny(
        num_classes=num_classes,
        freeze_backbone=freeze_backbone
    )
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=learning_rate,
        weight_decay=weight_decay
    )

    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.5,
        patience=3
    )

    # ===============================
    # Training loop
    # ===============================
    best_val_acc = 0.0
    best_epoch = 0

    history = {
        "train_loss": [],
        "train_acc": [],
        "val_loss": [],
        "val_acc": []
    }

    for epoch in range(num_epochs):
        train_loss, train_acc = train_one_epoch(
            model=model,
            dataloader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device
        )

        val_loss, val_acc, _, _ = evaluate(
            model=model,
            dataloader=val_loader,
            criterion=criterion,
            device=device
        )

        scheduler.step(val_acc)

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)

        print(
            f"Epoch [{epoch + 1}/{num_epochs}] "
            f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f} | "
            f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}"
        )

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_epoch = epoch + 1

            torch.save({
                "model_state_dict": model.state_dict(),
                "label_map": label_map,
                "class_names": class_names,
                "best_val_acc": best_val_acc,
                "best_epoch": best_epoch,
                "config": {
                    "model": "convnext_tiny",
                    "batch_size": batch_size,
                    "image_size": image_size,
                    "num_epochs": num_epochs,
                    "learning_rate": learning_rate,
                    "weight_decay": weight_decay,
                    "freeze_backbone": freeze_backbone,
                    "label_column": "class",
                    "image_column": "path_rgb_masked"
                }
            }, model_save_path)

            print(f"Best model saved at epoch {best_epoch} with val acc {best_val_acc:.4f}")

    # ===============================
    # Save training history
    # ===============================
    save_json(history, os.path.join(save_dir, "training_history.json"))

    # ===============================
    # Load best model for final test
    # ===============================
    checkpoint = torch.load(model_save_path, map_location=device)

    model = build_convnext_tiny(
        num_classes=num_classes,
        freeze_backbone=freeze_backbone
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model = model.to(device)

    test_loss, test_acc, y_true, y_pred = evaluate(
        model=model,
        dataloader=test_loader,
        criterion=criterion,
        device=device
    )

    report = classification_report(
        y_true,
        y_pred,
        target_names=class_names,
        output_dict=True,
        zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred)

    final_results = {
        "model": "convnext_tiny",
        "best_epoch": best_epoch,
        "best_val_acc": best_val_acc,
        "test_loss": test_loss,
        "test_acc": test_acc,
        "class_names": class_names,
        "label_map": label_map,
        "classification_report": report,
        "confusion_matrix": cm.tolist(),
        "config": {
            "batch_size": batch_size,
            "image_size": image_size,
            "num_epochs": num_epochs,
            "learning_rate": learning_rate,
            "weight_decay": weight_decay,
            "freeze_backbone": freeze_backbone,
            "label_column": "class",
            "image_column": "path_rgb_masked"
        }
    }

    save_json(final_results, os.path.join(save_dir, "final_results.json"))
    save_json(report, os.path.join(save_dir, "classification_report.json"))
    save_json({"confusion_matrix": cm.tolist(), "class_names": class_names}, os.path.join(save_dir, "confusion_matrix.json"))

    print("\n==============================")
    print("Final Test Result")
    print("==============================")
    print(f"Best Epoch    : {best_epoch}")
    print(f"Best Val Acc  : {best_val_acc:.4f}")
    print(f"Test Loss     : {test_loss:.4f}")
    print(f"Test Accuracy : {test_acc:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred, target_names=class_names, zero_division=0))
    print("\nConfusion Matrix:")
    print(cm)


if __name__ == "__main__":
    main()
