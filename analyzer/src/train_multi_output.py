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
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler

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

    if torch.cuda.is_available():
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

class ColorMultiOutputDataset(Dataset):
    def __init__(self, dataframe, image_base_dir, season_label_map, subclass_label_map, transform=None):
        self.dataframe = dataframe.reset_index(drop=True)
        self.image_base_dir = image_base_dir
        self.season_label_map = season_label_map
        self.subclass_label_map = subclass_label_map
        self.transform = transform

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, index):
        row = self.dataframe.iloc[index]

        image_path = os.path.join(self.image_base_dir, row["path_rgb_masked"])
        image = Image.open(image_path).convert("RGB")

        season_name = row["class"]
        subclass_name = row["sub_class"]

        season_label = self.season_label_map[season_name]
        subclass_label = self.subclass_label_map[subclass_name]

        if self.transform:
            image = self.transform(image)

        return image, season_label, subclass_label


# =====================================================
# Transforms
# =====================================================

def get_transforms():
    """
    Augmentasi dibuat ringan karena color analysis sensitif terhadap warna.
    Tidak memakai ColorJitter agar karakter warna asli tidak terlalu berubah.
    """

    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(4),
        transforms.RandomAffine(
            degrees=0,
            translate=(0.02, 0.02),
            scale=(0.98, 1.02)
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
# Weight helper
# =====================================================

def compute_class_weights(dataframe, label_column, label_map):
    """
    Membuat class weight agar kelas yang lebih sulit / lebih sedikit
    tidak terlalu kalah oleh kelas yang sering dipilih model.
    """

    counts = dataframe[label_column].value_counts()
    total = len(dataframe)
    num_classes = len(label_map)

    weights = []

    for class_name, index in sorted(label_map.items(), key=lambda item: item[1]):
        class_count = counts.get(class_name, 0)

        if class_count == 0:
            weight = 1.0
        else:
            weight = total / (num_classes * class_count)

        weights.append(weight)

    return torch.tensor(weights, dtype=torch.float32)


def create_combined_sampler(dataframe):
    """
    Balanced sampler berdasarkan kombinasi season + subclass.

    Tujuannya agar kombinasi seperti:
    - autunno_deep
    - inverno_deep
    - primavera_light
    - estate_light

    tidak terlalu kalah selama training.
    """

    combined_labels = dataframe["class"].astype(str) + "_" + dataframe["sub_class"].astype(str)
    label_counts = combined_labels.value_counts().to_dict()

    sample_weights = combined_labels.map(lambda label: 1.0 / label_counts[label]).values
    sample_weights = torch.DoubleTensor(sample_weights)

    sampler = WeightedRandomSampler(
        weights=sample_weights,
        num_samples=len(sample_weights),
        replacement=True
    )

    return sampler


# =====================================================
# Dataloaders
# =====================================================

def create_multi_output_dataloaders(
    csv_path="data/raw/annotations.csv",
    image_base_dir="data/raw/images",
    batch_size=16,
    val_size=0.2,
    random_state=42,
    num_workers=0,
    use_balanced_sampler=True
):
    df = pd.read_csv(csv_path)

    required_columns = ["class", "sub_class", "partition", "path_rgb_masked"]
    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Column '{column}' tidak ditemukan di annotations.csv")

    df = df.dropna(subset=required_columns).reset_index(drop=True)

    season_label_map = {
        "primavera": 0,
        "estate": 1,
        "autunno": 2,
        "inverno": 3
    }

    subclass_names = sorted(df["sub_class"].unique().tolist())
    subclass_label_map = {name: index for index, name in enumerate(subclass_names)}

    season_class_names = [
        name for name, _ in sorted(season_label_map.items(), key=lambda item: item[1])
    ]

    subclass_class_names = [
        name for name, _ in sorted(subclass_label_map.items(), key=lambda item: item[1])
    ]

    trainval_df = df[df["partition"] == "train"].copy().reset_index(drop=True)
    test_df = df[df["partition"] == "test"].copy().reset_index(drop=True)

    trainval_df["stratify_label"] = (
        trainval_df["class"].astype(str) + "_" + trainval_df["sub_class"].astype(str)
    )

    train_df, val_df = train_test_split(
        trainval_df,
        test_size=val_size,
        random_state=random_state,
        stratify=trainval_df["stratify_label"]
    )

    train_df = train_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)

    train_transform, eval_transform = get_transforms()

    train_dataset = ColorMultiOutputDataset(
        dataframe=train_df,
        image_base_dir=image_base_dir,
        season_label_map=season_label_map,
        subclass_label_map=subclass_label_map,
        transform=train_transform
    )

    val_dataset = ColorMultiOutputDataset(
        dataframe=val_df,
        image_base_dir=image_base_dir,
        season_label_map=season_label_map,
        subclass_label_map=subclass_label_map,
        transform=eval_transform
    )

    test_dataset = ColorMultiOutputDataset(
        dataframe=test_df,
        image_base_dir=image_base_dir,
        season_label_map=season_label_map,
        subclass_label_map=subclass_label_map,
        transform=eval_transform
    )

    if use_balanced_sampler:
        train_sampler = create_combined_sampler(train_df)

        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            sampler=train_sampler,
            shuffle=False,
            num_workers=num_workers
        )
    else:
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

    season_class_weights = compute_class_weights(
        dataframe=train_df,
        label_column="class",
        label_map=season_label_map
    )

    subclass_class_weights = compute_class_weights(
        dataframe=train_df,
        label_column="sub_class",
        label_map=subclass_label_map
    )

    return (
        train_loader,
        val_loader,
        test_loader,
        season_label_map,
        subclass_label_map,
        season_class_names,
        subclass_class_names,
        season_class_weights,
        subclass_class_weights
    )


# =====================================================
# Multi-output ConvNeXt-Tiny Model
# =====================================================

class ConvNeXtTinyMultiOutput(nn.Module):
    def __init__(self, num_season_classes=4, num_subclass_classes=6, pretrained=True, dropout=0.3):
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


# =====================================================
# Train and Evaluation
# =====================================================

def train_one_epoch(
    model,
    dataloader,
    criterion_season,
    criterion_subclass,
    optimizer,
    device,
    subclass_loss_weight=0.8
):
    model.train()

    running_loss = 0.0

    season_true = []
    season_pred = []
    subclass_true = []
    subclass_pred = []

    progress_bar = tqdm(dataloader, desc="Training", leave=True)

    for images, season_labels, subclass_labels in progress_bar:
        images = images.to(device)
        season_labels = season_labels.to(device)
        subclass_labels = subclass_labels.to(device)

        optimizer.zero_grad()

        season_outputs, subclass_outputs = model(images)

        loss_season = criterion_season(season_outputs, season_labels)
        loss_subclass = criterion_subclass(subclass_outputs, subclass_labels)

        loss = loss_season + (subclass_loss_weight * loss_subclass)

        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)

        season_preds = torch.argmax(season_outputs, dim=1)
        subclass_preds = torch.argmax(subclass_outputs, dim=1)

        season_true.extend(season_labels.detach().cpu().numpy())
        season_pred.extend(season_preds.detach().cpu().numpy())
        subclass_true.extend(subclass_labels.detach().cpu().numpy())
        subclass_pred.extend(subclass_preds.detach().cpu().numpy())

        current_loss = running_loss / len(season_true)
        current_season_acc = accuracy_score(season_true, season_pred)
        current_subclass_acc = accuracy_score(subclass_true, subclass_pred)

        progress_bar.set_postfix({
            "loss": f"{current_loss:.4f}",
            "season_acc": f"{current_season_acc:.4f}",
            "sub_acc": f"{current_subclass_acc:.4f}"
        })

    epoch_loss = running_loss / len(dataloader.dataset)
    epoch_season_acc = accuracy_score(season_true, season_pred)
    epoch_subclass_acc = accuracy_score(subclass_true, subclass_pred)

    return epoch_loss, epoch_season_acc, epoch_subclass_acc


@torch.no_grad()
def evaluate(
    model,
    dataloader,
    criterion_season,
    criterion_subclass,
    device,
    subclass_loss_weight=0.8,
    desc="Validation"
):
    model.eval()

    running_loss = 0.0

    season_true = []
    season_pred = []
    subclass_true = []
    subclass_pred = []

    progress_bar = tqdm(dataloader, desc=desc, leave=True)

    for images, season_labels, subclass_labels in progress_bar:
        images = images.to(device)
        season_labels = season_labels.to(device)
        subclass_labels = subclass_labels.to(device)

        season_outputs, subclass_outputs = model(images)

        loss_season = criterion_season(season_outputs, season_labels)
        loss_subclass = criterion_subclass(subclass_outputs, subclass_labels)

        loss = loss_season + (subclass_loss_weight * loss_subclass)

        running_loss += loss.item() * images.size(0)

        season_preds = torch.argmax(season_outputs, dim=1)
        subclass_preds = torch.argmax(subclass_outputs, dim=1)

        season_true.extend(season_labels.detach().cpu().numpy())
        season_pred.extend(season_preds.detach().cpu().numpy())
        subclass_true.extend(subclass_labels.detach().cpu().numpy())
        subclass_pred.extend(subclass_preds.detach().cpu().numpy())

        current_loss = running_loss / len(season_true)
        current_season_acc = accuracy_score(season_true, season_pred)
        current_subclass_acc = accuracy_score(subclass_true, subclass_pred)

        progress_bar.set_postfix({
            "loss": f"{current_loss:.4f}",
            "season_acc": f"{current_season_acc:.4f}",
            "sub_acc": f"{current_subclass_acc:.4f}"
        })

    epoch_loss = running_loss / len(dataloader.dataset)
    epoch_season_acc = accuracy_score(season_true, season_pred)
    epoch_subclass_acc = accuracy_score(subclass_true, subclass_pred)

    return (
        epoch_loss,
        epoch_season_acc,
        epoch_subclass_acc,
        season_true,
        season_pred,
        subclass_true,
        subclass_pred
    )


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
    num_epochs = 25
    learning_rate = 3e-5
    weight_decay = 1e-4
    val_size = 0.2
    num_workers = 0
    dropout = 0.3

    # Subclass tetap dilatih, tapi season dibuat lebih dominan
    # karena final color type sangat bergantung pada season.
    subclass_loss_weight = 0.8

    # Pemilihan best model lebih berat ke season.
    season_score_weight = 0.65
    subclass_score_weight = 0.35

    use_balanced_sampler = True

    save_dir = "results/convnext_tiny_multi_output"
    model_save_path = "models/convnext_tiny_multi_output.pth"

    os.makedirs(save_dir, exist_ok=True)
    os.makedirs("models", exist_ok=True)

    device = get_device()
    print(f"Using device: {device}")

    (
        train_loader,
        val_loader,
        test_loader,
        season_label_map,
        subclass_label_map,
        season_class_names,
        subclass_class_names,
        season_class_weights,
        subclass_class_weights
    ) = create_multi_output_dataloaders(
        csv_path=csv_path,
        image_base_dir=image_base_dir,
        batch_size=batch_size,
        val_size=val_size,
        num_workers=num_workers,
        use_balanced_sampler=use_balanced_sampler
    )

    season_class_weights = season_class_weights.to(device)
    subclass_class_weights = subclass_class_weights.to(device)

    print("Season class names:", season_class_names)
    print("Subclass class names:", subclass_class_names)
    print("Season label map:", season_label_map)
    print("Subclass label map:", subclass_label_map)
    print("Season class weights:", season_class_weights.detach().cpu().numpy())
    print("Subclass class weights:", subclass_class_weights.detach().cpu().numpy())
    print("Train samples:", len(train_loader.dataset))
    print("Val samples:", len(val_loader.dataset))
    print("Test samples:", len(test_loader.dataset))

    model = ConvNeXtTinyMultiOutput(
        num_season_classes=len(season_class_names),
        num_subclass_classes=len(subclass_class_names),
        pretrained=True,
        dropout=dropout
    ).to(device)

    criterion_season = nn.CrossEntropyLoss(
        weight=season_class_weights,
        label_smoothing=0.03
    )

    criterion_subclass = nn.CrossEntropyLoss(
        weight=subclass_class_weights,
        label_smoothing=0.03
    )

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

    best_val_score = 0.0
    best_epoch = 0
    patience = 7
    patience_counter = 0

    history = {
        "train_loss": [],
        "train_season_acc": [],
        "train_subclass_acc": [],
        "val_loss": [],
        "val_season_acc": [],
        "val_subclass_acc": [],
        "val_score": [],
        "learning_rate": []
    }

    for epoch in range(num_epochs):
        print(f"\nEpoch {epoch + 1}/{num_epochs}")

        train_loss, train_season_acc, train_subclass_acc = train_one_epoch(
            model=model,
            dataloader=train_loader,
            criterion_season=criterion_season,
            criterion_subclass=criterion_subclass,
            optimizer=optimizer,
            device=device,
            subclass_loss_weight=subclass_loss_weight
        )

        (
            val_loss,
            val_season_acc,
            val_subclass_acc,
            _, _, _, _
        ) = evaluate(
            model=model,
            dataloader=val_loader,
            criterion_season=criterion_season,
            criterion_subclass=criterion_subclass,
            device=device,
            subclass_loss_weight=subclass_loss_weight,
            desc="Validation"
        )

        val_score = (
            season_score_weight * val_season_acc
        ) + (
            subclass_score_weight * val_subclass_acc
        )

        scheduler.step(val_score)
        current_lr = optimizer.param_groups[0]["lr"]

        history["train_loss"].append(train_loss)
        history["train_season_acc"].append(train_season_acc)
        history["train_subclass_acc"].append(train_subclass_acc)
        history["val_loss"].append(val_loss)
        history["val_season_acc"].append(val_season_acc)
        history["val_subclass_acc"].append(val_subclass_acc)
        history["val_score"].append(val_score)
        history["learning_rate"].append(current_lr)

        print(f"Train Loss        : {train_loss:.4f}")
        print(f"Train Season Acc  : {train_season_acc:.4f}")
        print(f"Train Subclass Acc: {train_subclass_acc:.4f}")
        print(f"Val Loss          : {val_loss:.4f}")
        print(f"Val Season Acc    : {val_season_acc:.4f}")
        print(f"Val Subclass Acc  : {val_subclass_acc:.4f}")
        print(f"Val Score         : {val_score:.4f}")
        print(f"Learning Rate     : {current_lr:.8f}")

        if val_score > best_val_score:
            best_val_score = val_score
            best_epoch = epoch + 1
            patience_counter = 0

            torch.save({
                "model_state_dict": model.state_dict(),
                "season_label_map": season_label_map,
                "subclass_label_map": subclass_label_map,
                "season_class_names": season_class_names,
                "subclass_class_names": subclass_class_names,
                "best_val_score": best_val_score,
                "best_epoch": best_epoch,
                "config": {
                    "model": "convnext_tiny_multi_output",
                    "batch_size": batch_size,
                    "num_epochs": num_epochs,
                    "learning_rate": learning_rate,
                    "weight_decay": weight_decay,
                    "dropout": dropout,
                    "subclass_loss_weight": subclass_loss_weight,
                    "season_score_weight": season_score_weight,
                    "subclass_score_weight": subclass_score_weight,
                    "use_balanced_sampler": use_balanced_sampler,
                    "label_smoothing": 0.03,
                    "csv_path": csv_path,
                    "image_base_dir": image_base_dir
                }
            }, model_save_path)

            print(f"Best model saved at epoch {best_epoch} with val score {best_val_score:.4f}")
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

    model = ConvNeXtTinyMultiOutput(
        num_season_classes=len(season_class_names),
        num_subclass_classes=len(subclass_class_names),
        pretrained=False,
        dropout=dropout
    ).to(device)

    model.load_state_dict(checkpoint["model_state_dict"])

    (
        test_loss,
        test_season_acc,
        test_subclass_acc,
        season_true,
        season_pred,
        subclass_true,
        subclass_pred
    ) = evaluate(
        model=model,
        dataloader=test_loader,
        criterion_season=criterion_season,
        criterion_subclass=criterion_subclass,
        device=device,
        subclass_loss_weight=subclass_loss_weight,
        desc="Testing"
    )

    season_report = classification_report(
        season_true,
        season_pred,
        target_names=season_class_names,
        output_dict=True,
        zero_division=0
    )

    subclass_report = classification_report(
        subclass_true,
        subclass_pred,
        target_names=subclass_class_names,
        output_dict=True,
        zero_division=0
    )

    season_cm = confusion_matrix(season_true, season_pred)
    subclass_cm = confusion_matrix(subclass_true, subclass_pred)

    final_results = {
        "model": "convnext_tiny_multi_output",
        "best_epoch": best_epoch,
        "best_val_score": best_val_score,
        "test_loss": test_loss,
        "test_season_acc": test_season_acc,
        "test_subclass_acc": test_subclass_acc,
        "season_class_names": season_class_names,
        "subclass_class_names": subclass_class_names,
        "season_label_map": season_label_map,
        "subclass_label_map": subclass_label_map,
        "season_classification_report": season_report,
        "subclass_classification_report": subclass_report,
        "season_confusion_matrix": season_cm.tolist(),
        "subclass_confusion_matrix": subclass_cm.tolist()
    }

    save_json(final_results, os.path.join(save_dir, "final_results.json"))
    save_json(season_report, os.path.join(save_dir, "season_classification_report.json"))
    save_json(subclass_report, os.path.join(save_dir, "subclass_classification_report.json"))

    save_json(
        {
            "class_names": season_class_names,
            "confusion_matrix": season_cm.tolist()
        },
        os.path.join(save_dir, "season_confusion_matrix.json")
    )

    save_json(
        {
            "class_names": subclass_class_names,
            "confusion_matrix": subclass_cm.tolist()
        },
        os.path.join(save_dir, "subclass_confusion_matrix.json")
    )

    print("\n==============================")
    print("Final Test Result")
    print("==============================")
    print(f"Best Epoch        : {best_epoch}")
    print(f"Best Val Score    : {best_val_score:.4f}")
    print(f"Test Loss         : {test_loss:.4f}")
    print(f"Test Season Acc   : {test_season_acc:.4f}")
    print(f"Test Subclass Acc : {test_subclass_acc:.4f}")

    print("\nSeason Classification Report:")
    print(
        classification_report(
            season_true,
            season_pred,
            target_names=season_class_names,
            zero_division=0
        )
    )

    print("\nSubclass Classification Report:")
    print(
        classification_report(
            subclass_true,
            subclass_pred,
            target_names=subclass_class_names,
            zero_division=0
        )
    )

    print("\nSeason Confusion Matrix:")
    print(season_cm)

    print("\nSubclass Confusion Matrix:")
    print(subclass_cm)


if __name__ == "__main__":
    main()