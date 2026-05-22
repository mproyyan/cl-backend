import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm

from dataset import create_dataloaders
from model import build_efficientnetv2_s, get_device


def train_one_epoch(model, train_loader, criterion, optimizer, device):
    model.train()

    running_loss = 0.0
    correct = 0
    total = 0

    for images, labels in tqdm(train_loader, desc="Training"):
        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)
        loss = criterion(outputs, labels)

        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)

        _, predicted = torch.max(outputs, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

    epoch_loss = running_loss / total
    epoch_acc = correct / total

    return epoch_loss, epoch_acc


def evaluate(model, data_loader, criterion, device, desc="Validation"):
    model.eval()

    running_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in tqdm(data_loader, desc=desc):
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            loss = criterion(outputs, labels)

            running_loss += loss.item() * images.size(0)

            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    epoch_loss = running_loss / total
    epoch_acc = correct / total

    return epoch_loss, epoch_acc


def main():
    os.makedirs("models", exist_ok=True)
    os.makedirs("results", exist_ok=True)

    device = get_device()
    print("Device:", device)

    batch_size = 16
    num_epochs = 20
    learning_rate = 3e-5
    num_classes = 4
    unfreeze_last_blocks = 6

    train_loader, val_loader, test_loader, label_map = create_dataloaders(
        batch_size=batch_size,
        val_size=0.2
    )

    print("Label map:", label_map)
    print("Train batches:", len(train_loader))
    print("Val batches:", len(val_loader))
    print("Test batches:", len(test_loader))

    model = build_efficientnetv2_s(
        num_classes=num_classes,
        pretrained=True,
        freeze_backbone=True,
        unfreeze_last_blocks=unfreeze_last_blocks
    )
    model = model.to(device)

    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)

    optimizer = optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=learning_rate,
        weight_decay=1e-4
    )

    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        factor=0.5,
        patience=2
    )

    best_val_acc = 0.0
    patience = 6
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
            train_loader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device
        )

        val_loss, val_acc = evaluate(
            model=model,
            data_loader=val_loader,
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

        print(f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.4f}")
        print(f"Val Loss  : {val_loss:.4f} | Val Acc  : {val_acc:.4f}")
        print(f"Learning Rate: {current_lr:.8f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0

            torch.save({
                "model_state_dict": model.state_dict(),
                "label_map": label_map,
                "best_val_acc": best_val_acc,
                "batch_size": batch_size,
                "num_epochs": num_epochs,
                "learning_rate": learning_rate,
                "freeze_backbone": True,
                "unfreeze_last_blocks": unfreeze_last_blocks,
                "label_smoothing": 0.05
            }, "models/efficientnetv2_s_season.pth")

            print("Best model saved!")
        else:
            patience_counter += 1
            print(f"No improvement. Patience: {patience_counter}/{patience}")

        if patience_counter >= patience:
            print("Early stopping aktif. Training dihentikan.")
            break

    with open("results/training_history.json", "w") as f:
        json.dump(history, f, indent=4)

    print("\nTraining selesai.")
    print(f"Best Validation Accuracy: {best_val_acc:.4f}")
    print("Model terbaik disimpan di: models/efficientnetv2_s_season.pth")
    print("History training disimpan di: results/training_history.json")


if __name__ == "__main__":
    main()