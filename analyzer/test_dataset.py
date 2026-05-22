from src.dataset import create_dataloaders

train_loader, val_loader, test_loader, label_map = create_dataloaders(batch_size=16)

print("Label map:", label_map)
print("Jumlah batch train:", len(train_loader))
print("Jumlah batch val:", len(val_loader))
print("Jumlah batch test:", len(test_loader))

images, labels = next(iter(train_loader))

print("Shape images:", images.shape)
print("Shape labels:", labels.shape)
print("Contoh labels:", labels[:10])