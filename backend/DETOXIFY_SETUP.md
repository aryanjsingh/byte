# Detoxify Tool Setup

## What is Detoxify?

Detoxify is a Python library that uses trained models to detect toxic comments. It can identify:
- **Toxicity**: General toxic language
- **Severe Toxicity**: Very toxic language
- **Obscene**: Obscene or vulgar content
- **Threat**: Threatening language
- **Insult**: Insulting language
- **Identity Attack**: Hate speech targeting identity groups

## Installation

```bash
# Activate your virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install detoxify
pip install detoxify
```

This will install:
- `detoxify` - The main library
- `transformers` - Hugging Face transformers (for the model)
- `torch` - PyTorch (deep learning framework)

**Note**: The first time you use the tool, it will download the model (~500MB). This is a one-time download.

## Usage in Chat

The AI will automatically use this tool when users ask about toxic content:

**Example queries:**
- "Is this comment toxic: [text]"
- "Check if this message is offensive"
- "Does this contain hate speech?"
- "Analyze this for cyberbullying"
- "Is this appropriate for a community forum?"

## Tool Output

The tool provides:
- **Toxicity scores** for 6 categories (0-100%)
- **Risk assessment**: Safe, Low Risk, Moderate Risk, or High Risk
- **Recommendations** for content moderation

## Example Output

```
🛡️ Toxicity Analysis Report

📝 Text Analyzed: "You're an idiot and should be banned"

📊 Toxicity Scores:
  🔴 Toxicity: 89.5%
  ⚠️  Severe Toxicity: 12.3%
  😡 Obscene: 5.2%
  👎 Threat: 3.1%
  😠 Insult: 92.7%
  🚫 Identity Attack: 2.4%

💡 Assessment:
⛔ HIGH RISK - This content shows high levels of insult (92.7%). 
This type of content may violate community guidelines and could be harmful.
```

## Models Available

Detoxify supports three models:
- `original` (default): Trained on Wikipedia comments
- `unbiased`: Reduced bias against identity mentions
- `multilingual`: Supports multiple languages

The tool uses the `original` model by default for best performance.

## Use Cases

1. **Content Moderation**: Check user comments before posting
2. **Cyberbullying Detection**: Identify harmful messages
3. **Community Safety**: Monitor forum/chat content
4. **Hate Speech Detection**: Flag identity-based attacks
5. **Workplace Safety**: Detect harassment in communications

## Privacy Note

All analysis is done locally on your machine. No data is sent to external services.
