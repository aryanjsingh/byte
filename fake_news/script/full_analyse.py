from inference import predict_fake_news
from module_2 import analyze_emotions
from module_3 import assess_political_bias

# -----------------------------
# Full analysis pipeline
# -----------------------------
def analyze_news(text, source=None):
    # Module 1: Fake news detection
    veracity = predict_fake_news(text)

    # Module 2: Emotion analysis
    emotions = analyze_emotions(text)

    # Module 3: Political bias & impact
    bias = assess_political_bias(
        veracity_label=veracity["veracity_label"],
        confidence=veracity["confidence_score"],
        emotion_scores=emotions
    )

    # Final structured output
    result = {
        "veracity_label": veracity["veracity_label"],
        "confidence_score": veracity["confidence_score"],
        "emotion_scores": emotions,
        "political_bias_indicator": {
            "manipulation_level": bias["manipulation_level"],
            "reason": bias["reason"]
        },
        "impact_category": bias["impact_category"],
        "explanation": generate_explanation(
            veracity, emotions, bias, source
        )
    }

    return result


# -----------------------------
# Explanation generator
# -----------------------------
def generate_explanation(veracity, emotions, bias, source):
    parts = []

    parts.append(
        f"The content is classified as {veracity['veracity_label']} "
        f"with confidence {veracity['confidence_score']}."
    )

    if emotions["fear"] > 0.4:
        parts.append("The text contains fear-inducing language.")
    if emotions["anger"] > 0.4:
        parts.append("Anger-driven expressions are detected.")
    if emotions["urgency"] > 0.4:
        parts.append("Urgent or alarmist framing is present.")

    if bias["manipulation_level"] != "Low":
        parts.append(
            f"This results in a {bias['manipulation_level']} level of political manipulation."
        )

    if source:
        parts.append(f"The source provided is '{source}', which was not required for analysis.")

    return " ".join(parts)


# -----------------------------
# Test
# -----------------------------
if __name__ == "__main__":
    sample_text = (
        "The government is secretly planning to cancel elections, "
        "putting democracy and citizens at risk."
    )

    output = analyze_news(sample_text, source="Unknown Social Media Post")

    from pprint import pprint
    pprint(output)
