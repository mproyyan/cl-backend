import os
import json
import random
import numpy as np
import pandas as pd

from PIL import Image
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader

from torchvision import transforms, models

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix


# =====================================================
# Reproducibility
# =====================================================

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


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
# Dataset
# =====================================================

class ColorSubclassDataset(Dataset):
    def __init__(self, dataframe, image_base_dir, subclass_label_map, transform=None):
        self.dataframe = dataframe.reset_index(drop=True)
        self.image_base_dir = image_base_dir
        self.subclass_label_map = subclass_label_map
        self.transform = transform

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, index):
        row = self.dataframe.iloc[index]

        image_path = os.path.join(self.image_base_dir, row["path_rgb_masked"])
        image = Image.open(image_path).convert("RGB")

        subclass_name = row["sub_class"]
        subclass_label = self.subclass_label_map[subclass_name]

        if self.transform:
            image = self.transform(image)

        return image, subclass_label


# =====================================================
# Transforms
# =====================================================

def get_transforms():
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(5),
        transforms.RandomAffine(
            degrees=0,
            translate=(0.03, 0.03),
            scale=(0.97, 1.03)
        ),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    return train_transform, eval_transform


# =====================================================
# Dataloaders
# =====================================================

def create_subclass_dataloaders(
    csv_path="data/raw/annotations.csv",
    image_base_dir="data/raw/images",
    batch_size=16,
    val_size=0.2,
    random_state=42,
    num_workers=0
):
    df = pd.read_csv(csv_path)

    required_columns = ["class", "sub_class", "partition", "path_rgb_masked"]
    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' tidak ditemukan di annotations.csv")

    df = df.dropna(subset=required_columns).reset_index(drop=True)

    subclass_names = sorted(df["sub_class"].unique().tolist())
    subclass_label_map = {name: index for index, name in enumerate(subclass_names)}
    subclass_class_names = [name for name, _ in sorted(subclass_label_map.items(), key=lambda item: item[1])]

    trainval_df = df[df["partition"] == "train"].copy().reset_index(drop=True)
    test_df = df[df["partition"] == "test"].copy().reset_index(drop=True)

    train_df, val_df = train_test_split(
        trainval_df,
        test_size=val_size,
        random_state=random_state,
        stratify=trainval_df["sub_class"]
    )

    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)

    train_transform, eval_transform = get_transforms()

    train_dataset = ColorSubclassDataset(
        dataframe=train_df,
        image_base_dir=image_base_dir,
        subclass_label_map=subclass_label_map,
        transform=train_transform
    )

    val_dataset = ColorSubclassDataset(
        dataframe=val_df,
        image_base_dir=image_base_dir,
        subclass_label_map=subclass_label_map,
        transform=eval_transform
    )

    test_dataset = ColorSubclassDataset(
        dataframe=test_df,
        image_base_dir=image_base_dir,
        subclass_label_map=subclass_label_map,
        transform=eval_transform
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers
    )

    return train_loader, val_loader, test_loader, subclass_label_map, subclass_class_names


# =====================================================
# Model
# =====================================================

def build_convnext_tiny_subclass(num_classes=6, pretrained=True, dropout=0.4):
    weights = models.ConvNeXt_Tiny_Weights.DEFAULT if pretrained else None
    model = models.convnext_tiny(weights=weights)

    in_features = model.classifier[2].in_features

    model.classifier[2] = nn.Sequential(
        nn.Dropout(p=dropout),
        nn.Linear(in_features, num_classes)
    )

    return model


# =====================================================
# Train and evaluation
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

    epoch_loss = running_loss / len(dataloader.dataset)
    epoch_acc = accuracy_score(all_labels, all_preds)

    return epoch_loss, epoch_acc


@torch.no_grad()
def evaluate(model, dataloader, criterion, device, desc="Validation"):
    model.eval()

    running_loss = 0.0
    all_labels = []
    all_preds = []

    progress_bar = tqdm(dataloader, desc=desc, leave=True)

    for images, labels in progress_bar:
        images = images.to(device)
        labels = labels.to(device)

        outputs = model(images)
        loss = criterion(outputs, labels)

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

    epoch_loss = running_loss / len(dataloader.dataset)
    epoch_acc = accuracy_score(all_labels, all_preds)

    return epoch_loss, epoch_acc, all_labels, all_preds


# =====================================================
# Save helper
# =====================================================

def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# =====================================================
# Main
# =====================================================

def main():
    set_seed(42)

    # ===============================
    # Config
    # ===============================
    csv_path = "data/raw/annotations.csv"
    image_base_dir = "data/raw/images"

    batch_size = 16
    num_epochs = 20
    learning_rate = 5e-5
    weight_decay = 1e-4
    val_size = 0.2
    num_workers = 0
    dropout = 0.4
    patience = 6

    save_dir = "results/convnext_tiny_subclass_only"
    model_save_path = "models/convnext_tiny_subclass_only.pth"

    os.makedirs(save_dir, exist_ok=True)
    os.makedirs("models", exist_ok=True)

    device = get_device()
    print(f"Using device: {device}")

    train_loader, val_loader, test_loader, subclass_label_map, subclass_class_names = create_subclass_dataloaders(
        csv_path=csv_path,
        image_base_dir=image_base_dir,
        batch_size=batch_size,
        val_size=val_size,
        num_workers=num_workers
    )

    print("Subclass class names:", subclass_class_names)
    print("Subclass label map:", subclass_label_map)
    print("Train samples:", len(train_loader.dataset))
    print("Val samples:", len(val_loader.dataset))
    print("Test samples:", len(test_loader.dataset))

    model = build_convnext_tiny_subclass(
        num_classes=len(subclass_class_names),
        pretrained=True,
        dropout=dropout
    ).to(device)

    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)

    optimizer = optim.AdamW(
        model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay
    )

    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.5,
        patience=2
    )

    best_val_acc = 0.0
    best_epoch = 0
    patience_counter = 0

    history = {
        "train_loss": [],
        "train_acc": [],
        "val_loss": [],
        "val_acc": [],
        "learning_rate": []
    }

    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch + 1}/{num_epochs}")

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
            device=device,
            desc="Validation"
        )

        scheduler.step(val_acc)
        current_lr = optimizer.param_groups[0]["lr"]

        history["train_loss"].append(train_loss)
        history["train_acc"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_acc"].append(val_acc)
        history["learning_rate"].append(current_lr)

        print(f"Train Loss   : {train_loss:.4f}")
        print(f"Train Acc    : {train_acc:.4f}")
        print(f"Val Loss     : {val_loss:.4f}")
        print(f"Val Acc      : {val_acc:.4f}")
        print(f"Learning Rate: {current_lr:.8f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            best_epoch = epoch + 1
            patience_counter = 0

            torch.save({
                "model_state_dict": model.state_dict(),
                "subclass_label_map": subclass_label_map,
                "subclass_class_names": subclass_class_names,
                "best_val_acc": best_val_acc,
                "best_epoch": best_epoch,
                "config": {
                    "model": "convnext_tiny_subclass_only",
                    "batch_size": batch_size,
                    "num_epochs": num_epochs,
                    "learning_rate": learning_rate,
                    "weight_decay": weight_decay,
                    "dropout": dropout,
                    "csv_path": csv_path,
                    "image_base_dir": image_base_dir
                }
            }, model_save_path)

            print(f"Best model saved at epoch {best_epoch} with val acc {best_val_acc:.4f}")
        else:
            patience_counter += 1
            print(f"No improvement. Patience: {patience_counter}/{patience}")

        if patience_counter >= patience:
            print("Early stopping triggered.")
            break

    save_json(history, os.path.join(save_dir, "training_history.json"))

    # ===============================
    # Final test with best model
    # ===============================
    checkpoint = torch.load(model_save_path, map_location=device)

    model = build_convnext_tiny_subclass(
        num_classes=len(subclass_class_names),
        pretrained=False,
        dropout=dropout
    ).to(device)

    model.load_state_dict(checkpoint["model_state_dict"])

    test_loss, test_acc, y_true, y_pred = evaluate(
        model=model,
        dataloader=test_loader,
        criterion=criterion,
        device=device,
        desc="Testing"
    )

    report = classification_report(
        y_true,
        y_pred,
        target_names=subclass_class_names,
        output_dict=True,
        zero_division=0
    )

    cm = confusion_matrix(y_true, y_pred)

    final_results = {
        "model": "convnext_tiny_subclass_only",
        "best_epoch": best_epoch,
        "best_val_acc": best_val_acc,
        "test_loss": test_loss,
        "test_acc": test_acc,
        "subclass_class_names": subclass_class_names,
        "subclass_label_map": subclass_label_map,
        "classification_report": report,
        "confusion_matrix": cm.tolist()
    }

    save_json(final_results, os.path.join(save_dir, "final_results.json"))
    save_json(report, os.path.join(save_dir, "classification_report.json"))
    save_json(
        {"class_names": subclass_class_names, "confusion_matrix": cm.tolist()},
        os.path.join(save_dir, "confusion_matrix.json")
    )

    print("\n==============================")
    print("Final Test Result")
    print("==============================")
    print(f"Best Epoch     : {best_epoch}")
    print(f"Best Val Acc   : {best_val_acc:.4f}")
    print(f"Test Loss      : {test_loss:.4f}")
    print(f"Test Accuracy  : {test_acc:.4f}")

    print("\nSubclass Classification Report:")
    print(classification_report(y_true, y_pred, target_names=subclass_class_names, zero_division=0))

    print("\nSubclass Confusion Matrix:")
    print(cm)


if __name__ == "__main__":
    main()
