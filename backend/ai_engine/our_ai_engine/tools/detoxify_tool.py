"""
Detoxify Tool - Toxic Comment Detection
Uses the Detoxify library to detect toxic, threatening, obscene, insulting, and identity-based hate speech.
"""

from langchain_core.tools import tool

def _analyze_toxicity(text: str) -> str:
    """
    Analyze text for toxicity using Detoxify model.
    Returns formatted string result.
    """
    try:
        from detoxify import Detoxify
        
        # Initialize model (uses 'original' model by default)
        # Options: 'original', 'unbiased', 'multilingual'
        model = Detoxify('original')
        
        # Get predictions
        results = model.predict(text)
        
        # Format output
        output = f"""🛡️ Toxicity Analysis Report

📝 **Text Analyzed**: {text[:100]}{'...' if len(text) > 100 else ''}

📊 **Toxicity Scores**:
  🔴 Toxicity: {results['toxicity']:.1%}
  ⚠️  Severe Toxicity: {results['severe_toxicity']:.1%}
  😡 Obscene: {results['obscene']:.1%}
  👎 Threat: {results['threat']:.1%}
  😠 Insult: {results['insult']:.1%}
  🚫 Identity Attack: {results['identity_attack']:.1%}

💡 **Assessment**:
"""
        
        # Determine overall assessment
        max_score = max(results.values())
        max_category = max(results, key=results.get)
        
        if max_score > 0.7:
            output += f"⛔ **HIGH RISK** - This content shows high levels of {max_category.replace('_', ' ')} ({max_score:.1%}). "
            output += "This type of content may violate community guidelines and could be harmful."
        elif max_score > 0.5:
            output += f"⚠️ **MODERATE RISK** - This content contains moderate {max_category.replace('_', ' ')} ({max_score:.1%}). "
            output += "Consider reviewing and potentially moderating this content."
        elif max_score > 0.3:
            output += f"🟡 **LOW RISK** - This content has some indicators of {max_category.replace('_', ' ')} ({max_score:.1%}). "
            output += "Generally acceptable but may need context-based review."
        else:
            output += "✅ **SAFE** - This content appears to be non-toxic and appropriate. "
            output += "No significant toxicity indicators detected."
        
        return output
        
    except ImportError:
        return """Error: Detoxify library not installed.

To install, run:
pip install detoxify

This will install the required dependencies including transformers and torch."""
    except Exception as e:
        print(f"❌ Detoxify analysis error: {e}")
        import traceback
        traceback.print_exc()
        return f"Error analyzing text: {str(e)}"


@tool
def detoxify_analyze(text: str) -> str:
    """
    Analyze text content for toxicity, threats, obscenity, insults, and identity-based hate speech.
    Use this tool when users want to check if content is toxic, offensive, or violates community guidelines.
    
    Detects:
    - Toxicity (general toxic language)
    - Severe toxicity (very toxic language)
    - Obscene content
    - Threats
    - Insults
    - Identity-based attacks (hate speech)
    
    Returns:
    - Toxicity scores for each category (0-100%)
    - Overall risk assessment
    - Recommendations
    """
    print(f"🔧 TOOL CALLED: detoxify_analyze")
    print(f"📝 Text (first 100 chars): {text[:100]}...")
    
    result = _analyze_toxicity(text)
    print(f"✅ TOOL RESULT: Analysis complete")
    return result
