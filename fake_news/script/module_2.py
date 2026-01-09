import re

# -----------------------------
# Emotion lexicons (minimal but effective)
# -----------------------------
FEAR_WORDS = {
    "fear", "afraid", "threat", "danger", "panic", "terror", "scared",
    "attack", "kill", "war", "violence", "destroy", "risk"
}

ANGER_WORDS = {
    "anger", "angry", "outrage", "hate", "furious", "rage",
    "corrupt", "evil", "traitor", "liar", "disgust"
}

URGENCY_WORDS = {
    "now", "immediately", "urgent", "must", "act", "quick",
    "before it's too late", "breaking", "alert"
}

# -----------------------------
# Emotion scoring function
# -----------------------------
def analyze_emotions(text):
    text = text.lower()
    words = re.findall(r"\b\w+\b", text)

    total_words = max(len(words), 1)

    fear_score = sum(1 for w in words if w in FEAR_WORDS) / total_words
    anger_score = sum(1 for w in words if w in ANGER_WORDS) / total_words
    urgency_score = sum(1 for w in words if w in URGENCY_WORDS) / total_words

    # Normalize to 0–1 range
    return {
        "fear": round(min(fear_score * 10, 1.0), 3),
        "anger": round(min(anger_score * 10, 1.0), 3),
        "urgency": round(min(urgency_score * 10, 1.0), 3)
    }

# -----------------------------
# Test
# -----------------------------
if __name__ == "__main__":
    sample = "The government is secretly planning to cancel elections and people are in danger."
    print(analyze_emotions(sample))
