import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
import torch.nn.functional as F
import os

# -----------------------------
# 1. Load model & tokenizer
# -----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "output", "final_model")

tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_DIR)
model = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)

model.eval()  # inference mode

# Label mapping (VERY IMPORTANT)
LABEL_MAP = {
    0: "Fake",
    1: "Real",
    2: "Uncertain"
}

# -----------------------------
# 2. Prediction function
# -----------------------------
def predict_fake_news(text):
    inputs = tokenizer(
        text,
        truncation=True,
        padding="max_length",
        max_length=128,
        return_tensors="pt"
    )

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = F.softmax(logits, dim=1)

    confidence, predicted_class = torch.max(probs, dim=1)

    conf = confidence.item()
    pred_label = LABEL_MAP[predicted_class.item()]

    # Calibration logic
    if conf < 0.20:
        final_label = "Uncertain"
    else:
        final_label = pred_label

    return {
        "veracity_label": final_label,
        "confidence_score": round(conf, 4)
    }


# -----------------------------
# 3. Test examples
# -----------------------------
if __name__ == "__main__":
    test_texts = [
        "The government is secretly planning to cancel elections next year.",
        "The finance minister announced a new tax policy during the budget session.",
        "Experts say the policy may have mixed outcomes depending on implementation."
    ]

    for text in test_texts:
        result = predict_fake_news(text)
        print("\nTEXT:", text)
        print("PREDICTION:", result)
