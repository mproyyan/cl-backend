import pandas as pd
import os

csv_path = "data/raw/annotations.csv"

df = pd.read_csv(csv_path)

print("Jumlah data:", len(df))
print("\nKolom:")
print(df.columns)

print("\n5 data pertama:")
print(df.head())

print("\nJumlah class:")
print(df["class"].value_counts())

print("\nJumlah subclass:")
print(df["sub_class"].value_counts())

print("\nJumlah partition:")
print(df["partition"].value_counts())

print("\nCek path gambar:")

base_dir = "data/raw/images"

for i in range(10):
    img_path = os.path.join(base_dir, df.loc[i, "path_rgb_masked"])
    print(img_path, "=>", os.path.exists(img_path))