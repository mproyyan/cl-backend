import torch
import torch.nn as nn
from torchvision import models


def build_efficientnetv2_s(
    num_classes=4,
    pretrained=True,
    freeze_backbone=False,
    unfreeze_last_blocks=3
):
    if pretrained:
        weights = models.EfficientNet_V2_S_Weights.DEFAULT
    else:
        weights = None

    model = models.efficientnet_v2_s(weights=weights)

    # Freeze semua feature extractor dulu
    if freeze_backbone:
        for param in model.features.parameters():
            param.requires_grad = False

    # Buka beberapa block terakhir agar model bisa adaptasi ke dataset color analysis
    if unfreeze_last_blocks > 0:
        for block in model.features[-unfreeze_last_blocks:]:
            for param in block.parameters():
                param.requires_grad = True

    in_features = model.classifier[1].in_features

    model.classifier = nn.Sequential(
        nn.Dropout(p=0.4),
        nn.Linear(in_features, num_classes)
    )

    return model


def get_device():
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    else:
        return torch.device("cpu")


if __name__ == "__main__":
    device = get_device()

    model = build_efficientnetv2_s(
        num_classes=4,
        pretrained=True,
        freeze_backbone=True,
        unfreeze_last_blocks=3
    )

    model = model.to(device)

    dummy_input = torch.randn(1, 3, 224, 224).to(device)
    output = model(dummy_input)

    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print("Device:", device)
    print("Output shape:", output.shape)
    print("Total params:", total_params)
    print("Trainable params:", trainable_params)