"""
Fake News Detection Tool for BYTE Security Agent.
Uses trained DistilBERT model to detect fake news, analyze emotions,
and assess political manipulation in text content.
"""

import os
import sys
from langchain_core.tools import tool

# Add fake_news script directory to path
FAKE_NEWS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))),
    "fake_news", "script"
)
sys.path.insert(0, FAKE_NEWS_DIR)


def _analyze_fake_news(text: str) -> str:
    """
    Analyze text for fake news using the trained model.
    Returns formatted string result.
    """
    try:
        from full_analyse import analyze_news
        
        result = analyze_news(text)
        
        # Format output as readable string
        output = f"""📰 Fake News Analysis Report

🔍 **Veracity**: {result['veracity_label']}
📊 **Confidence**: {result['confidence_score']:.1%}

😨 **Emotion Scores**:
  - Fear: {result['emotion_scores']['fear']:.1%}
  - Anger: {result['emotion_scores']['anger']:.1%}
  - Urgency: {result['emotion_scores']['urgency']:.1%}

⚠️ **Political Manipulation**:
  - Level: {result['political_bias_indicator']['manipulation_level']}
  - Reason: {result['political_bias_indicator']['reason']}

📈 **Impact Category**: {result['impact_category']}

💡 **Explanation**: {result['explanation']}
"""
        return output
        
    except ImportError as e:
        return f"Error: Fake news model not properly configured. {str(e)}"
    except Exception as e:
        print(f"❌ Fake news analysis error: {e}")
        import traceback
        traceback.print_exc()
        return f"Error analyzing text: {str(e)}"


@tool
def fake_news_analyze(text: str) -> str:
    """
    Analyze text content for fake news indicators, emotional manipulation,
    and political bias. Use this tool when users share news articles,
    social media posts, or any text they want verified for authenticity.
    
    Returns:
    - Veracity label (Fake/Real/Uncertain)
    - Confidence score
    - Emotion analysis (fear, anger, urgency)
    - Political manipulation assessment
    - Detailed explanation
    """
    print(f"🔧 TOOL CALLED: fake_news_analyze")
    print(f"📝 Text (first 100 chars): {text[:100]}...")
    
    result = _analyze_fake_news(text)
    print(f"✅ TOOL RESULT: Analysis complete")
    return result
