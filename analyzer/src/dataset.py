import os
import pandas as pd
from PIL import Image

from sklearn.model_selection import train_test_split

from torch.utils.data import Dataset, DataLoader
from torchvision import transforms


class ColorSeasonDataset(Dataset):
    def __init__(self, dataframe, image_base_dir, label_map, transform=None):
        self.dataframe = dataframe.reset_index(drop=True)
        self.image_base_dir = image_base_dir
        self.label_map = label_map
        self.transform = transform

    def __len__(self):
        return len(self.dataframe)

    def __getitem__(self, index):
        row = self.dataframe.iloc[index]

        image_path = os.path.join(self.image_base_dir, row["path_rgb_masked"])
        image = Image.open(image_path).convert("RGB")

        label_name = row["class"]
        label = self.label_map[label_name]

        if self.transform:
            image = self.transform(image)

        return image, label


def get_transforms():
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),

        # Augmentasi ringan agar model tidak terlalu menghafal posisi wajah.
        # Dibuat ringan karena project ini sensitif terhadap warna kulit/wajah.
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


def create_dataloaders(
    csv_path="data/raw/annotations.csv",
    image_base_dir="data/raw/images",
    batch_size=16,
    val_size=0.2,
    random_state=42
):
    df = pd.read_csv(csv_path)

    label_map = {
        "primavera": 0,  # spring
        "estate": 1,     # summer
        "autunno": 2,    # autumn
        "inverno": 3     # winter
    }

    # Ambil data berdasarkan partition dari annotations.csv
    trainval_df = df[df["partition"] == "train"].copy()
    test_df = df[df["partition"] == "test"].copy()

    # Split train-val dibuat berdasarkan kombinasi class + sub_class
    # agar distribusi season dan karakter sub-season lebih seimbang.
    trainval_df["stratify_label"] = (
        trainval_df["class"].astype(str)
        + "_"
        + trainval_df["sub_class"].astype(str)
    )

    train_df, val_df = train_test_split(
        trainval_df,
        test_size=val_size,
        random_state=random_state,
        stratify=trainval_df["stratify_label"]
    )

    train_transform, eval_transform = get_transforms()

    train_dataset = ColorSeasonDataset(
        dataframe=train_df,
        image_base_dir=image_base_dir,
        label_map=label_map,
        transform=train_transform
    )

    val_dataset = ColorSeasonDataset(
        dataframe=val_df,
        image_base_dir=image_base_dir,
        label_map=label_map,
        transform=eval_transform
    )

    test_dataset = ColorSeasonDataset(
        dataframe=test_df,
        image_base_dir=image_base_dir,
        label_map=label_map,
        transform=eval_transform
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0
    )

    return train_loader, val_loader, test_loader, label_map