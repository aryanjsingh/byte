import pandas as pd
import matplotlib.pyplot as plt
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "final_dataset.csv")

df = pd.read_csv(DATA_PATH)

# -----------------------------
# 1. Text length analysis
# -----------------------------
df["text_length"] = df["text"].apply(lambda x: len(x.split()))

print("\nText Length Statistics:")
print(df["text_length"].describe())

# -----------------------------
# 2. Short vs Long categorization
# -----------------------------
def length_bucket(length):
    if length <= 50:
        return "Short (LIAR-like)"
    elif length <= 200:
        return "Medium"
    else:
        return "Long (WELFake-like)"

df["length_bucket"] = df["text_length"].apply(length_bucket)

print("\nLength Bucket Distribution:")
print(df["length_bucket"].value_counts())

print("\nLabel vs Length Bucket:")
print(pd.crosstab(df["label"], df["length_bucket"]))

# -----------------------------
# 3. Plot distribution (visual sanity check)
# -----------------------------
plt.figure()
df["text_length"].hist(bins=100)
plt.xlabel("Number of Words")
plt.ylabel("Frequency")
plt.title("Text Length Distribution")
plt.show()
