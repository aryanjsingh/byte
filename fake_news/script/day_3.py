import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_class_weight
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments
)
from datasets import Dataset
import numpy as np
import os

# -----------------------------
# 0. Device check
# -----------------------------
device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)

# -----------------------------
# 1. Load dataset
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "processed", "final_dataset.csv")

df = pd.read_csv(DATA_PATH)

# OPTIONAL SPEED SAMPLING (still balanced & safe)
df = df.sample(n=20000, random_state=42)

label_encoder = LabelEncoder()
df["labels"] = label_encoder.fit_transform(df["label"])

print("Labels:", label_encoder.classes_)

# -----------------------------
# 2. Train-test split
# -----------------------------
train_df, test_df = train_test_split(
    df,
    test_size=0.15,
    random_state=42,
    stratify=df["labels"]
)

# -----------------------------
# 3. HF Dataset
# -----------------------------
train_ds = Dataset.from_pandas(train_df[["text", "labels"]])
test_ds  = Dataset.from_pandas(test_df[["text", "labels"]])

# -----------------------------
# 4. Tokenizer (FAST SETTINGS)
# -----------------------------
tokenizer = DistilBertTokenizerFast.from_pretrained(
    "distilbert-base-uncased"
)

def tokenize(batch):
    return tokenizer(
        batch["text"],
        truncation=True,
        padding="max_length",
        max_length=128   # 🔥 HUGE SPEED GAIN
    )

train_ds = train_ds.map(tokenize, batched=True, remove_columns=["text"])
test_ds  = test_ds.map(tokenize, batched=True, remove_columns=["text"])

train_ds.set_format("torch")
test_ds.set_format("torch")

# -----------------------------
# 5. Class weights
# -----------------------------
class_weights = compute_class_weight(
    class_weight="balanced",
    classes=np.unique(train_df["labels"]),
    y=train_df["labels"]
)
class_weights = torch.tensor(class_weights, dtype=torch.float).to(device)

# -----------------------------
# 6. Model
# -----------------------------
model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=len(label_encoder.classes_)
)

# 🔥 FREEZE ENCODER (KEY SPEED FIX)
for param in model.distilbert.parameters():
    param.requires_grad = False

model.to(device)

# -----------------------------
# 7. Custom Trainer (STABLE)
# -----------------------------
class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits

        loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights)
        loss = loss_fn(logits, labels)

        return (loss, outputs) if return_outputs else loss

# -----------------------------
# 8. Training arguments (FAST)
# -----------------------------
training_args = TrainingArguments(
    output_dir=os.path.join(BASE_DIR, "output", "model"),
    learning_rate=5e-4,                # higher LR (head only)
    per_device_train_batch_size=32,
    per_device_eval_batch_size=32,
    num_train_epochs=1,                # 🔥 1 epoch is enough
    fp16=torch.cuda.is_available(),
    logging_steps=100,
    save_strategy="no",
    report_to="none"
)

# -----------------------------
# 9. Train
# -----------------------------
trainer = WeightedTrainer(
    model=model,
    args=training_args,
    train_dataset=train_ds,
    eval_dataset=test_ds
)

trainer.train()

# -----------------------------
# 10. Save model
# -----------------------------
FINAL_MODEL_DIR = os.path.join(BASE_DIR, "output", "final_model")
os.makedirs(FINAL_MODEL_DIR, exist_ok=True)

model.save_pretrained(FINAL_MODEL_DIR)
tokenizer.save_pretrained(FINAL_MODEL_DIR)

print("✅ FAST TRAINING COMPLETED")
print("Model saved to:", FINAL_MODEL_DIR)
