def assess_political_bias(veracity_label, confidence, emotion_scores):
    fear = emotion_scores["fear"]
    anger = emotion_scores["anger"]
    urgency = emotion_scores["urgency"]

    emotional_intensity = fear + anger + urgency

    # -----------------------------
    # Manipulation logic
    # -----------------------------
    if veracity_label == "Fake" and emotional_intensity > 0.6:
        manipulation = "High"
        reason = "Fake or misleading content combined with strong emotional language."

    elif veracity_label == "Uncertain" and emotional_intensity > 0.7:
        manipulation = "High"
        reason = "Unverifiable political claim framed with emotionally manipulative language."

    elif emotional_intensity > 0.4:
        manipulation = "Medium"
        reason = "Emotionally charged language that may influence political opinion."

    else:
        manipulation = "Low"
        reason = "Neutral or factual language with low emotional influence."

    # -----------------------------
    # Impact estimation
    # -----------------------------
    if manipulation == "High":
        impact = "High"
    elif manipulation == "Medium":
        impact = "Medium"
    else:
        impact = "Low"

    return {
        "manipulation_level": manipulation,
        "reason": reason,
        "impact_category": impact
    }


# -----------------------------
# Test
# -----------------------------
if __name__ == "__main__":
    sample_veracity = "Uncertain"
    sample_confidence = 0.83
    sample_emotions = {"fear": 0.6, "anger": 0.2, "urgency": 0.1}

    result = assess_political_bias(
        sample_veracity,
        sample_confidence,
        sample_emotions
    )

    print(result)
