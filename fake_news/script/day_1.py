import pandas as pd
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_DIR = os.path.join(BASE_DIR, "data", "raw")
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# -----------------------------
# 1. PROCESS WELFAKE DATASET
# -----------------------------
welfake_path = os.path.join(RAW_DATA_DIR, "WELFake_Dataset.csv")
welfake_df = pd.read_csv(welfake_path)

# Keep only required columns
welfake_df = welfake_df[["title", "text", "label"]]

# Combine title + text (IMPORTANT for accuracy)
welfake_df["text"] = welfake_df["title"].fillna("") + " " + welfake_df["text"].fillna("")

# Map labels
# 1 -> Fake, 0 -> Real
welfake_df["label"] = welfake_df["label"].map({1: "Fake", 0: "Real"})

welfake_df = welfake_df[["text", "label"]]

print("WELFake samples:", len(welfake_df))


# -----------------------------
# 2. PROCESS LIAR DATASET
# -----------------------------
liar_dir = os.path.join(RAW_DATA_DIR, "liar_dataset")

def load_liar_split(file_name):
    path = os.path.join(liar_dir, file_name)
    df = pd.read_csv(path, sep="\t", header=None)
    df.columns = [
        "id", "label", "statement", "subject", "speaker",
        "job", "state", "party",
        "barely_true", "false", "half_true",
        "mostly_true", "pants_fire", "context"
    ]
    return df[["statement", "label"]]

liar_train = load_liar_split("train.tsv")
liar_valid = load_liar_split("valid.tsv")
liar_test = load_liar_split("test.tsv")

liar_df = pd.concat([liar_train, liar_valid, liar_test], ignore_index=True)

# Normalize LIAR labels
def normalize_liar_label(label):
    if label in ["true", "mostly-true"]:
        return "Real"
    elif label == "half-true":
        return "Uncertain"
    else:
        return "Fake"

liar_df["label"] = liar_df["label"].apply(normalize_liar_label)
liar_df.rename(columns={"statement": "text"}, inplace=True)

print("LIAR samples:", len(liar_df))


# -----------------------------
# 3. MERGE DATASETS
# -----------------------------
final_df = pd.concat([welfake_df, liar_df], ignore_index=True)

# Remove empty texts
final_df = final_df.dropna()
final_df = final_df[final_df["text"].str.len() > 30]

# Shuffle dataset
final_df = final_df.sample(frac=1, random_state=42).reset_index(drop=True)

# Save final dataset
output_path = os.path.join(PROCESSED_DATA_DIR, "final_dataset.csv")
final_df.to_csv(output_path, index=False)

print("Final dataset saved to:", output_path)
print(final_df["label"].value_counts())
