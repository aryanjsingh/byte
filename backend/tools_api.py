"""
Tools API - Standalone tool endpoints for URL Checker, Code Checker, Fake News, Quiz
"""
import re
import os
import random
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from dotenv import load_dotenv

from backend.database import get_session
from backend.models import User, ToolHistory, QuizAttempt
from backend.auth import get_current_user

load_dotenv()

router = APIRouter(prefix="/tools", tags=["tools"])

# ============== PYDANTIC MODELS ==============

class URLCheckRequest(BaseModel):
    target: str  # URL or IP address

class URLCheckResponse(BaseModel):
    target: str
    target_type: str  # url | ip
    is_safe: bool
    risk_level: str  # safe | low | medium | high | critical
    details: dict
    scan_id: Optional[int] = None

class CodeCheckRequest(BaseModel):
    code: str
    language: str = "python"  # python | javascript | java | php

class CodeCheckResponse(BaseModel):
    vulnerabilities: List[dict]
    risk_level: str
    total_issues: int
    suggestions: List[str]
    scan_id: Optional[int] = None

class FakeNewsRequest(BaseModel):
    content: str  # News headline or article text

class FakeNewsResponse(BaseModel):
    content: str
    verdict: str  # likely_fake | likely_real | uncertain
    confidence: float
    red_flags: List[str]
    analysis: str
    scan_id: Optional[int] = None

class QuizQuestion(BaseModel):
    id: int
    question: str
    options: List[str]
    category: str

class QuizStartRequest(BaseModel):
    category: str = "mixed"  # phishing | malware | social_engineering | upi_fraud | cyber_laws | mixed
    num_questions: int = 10

class QuizSubmitRequest(BaseModel):
    answers: List[dict]  # [{question_id: int, selected: int}]
    time_taken_seconds: int = 0
    quiz_id: Optional[str] = None  # For AI-generated quizzes

class ToxicityCheckRequest(BaseModel):
    text: str

class ToxicityCheckResponse(BaseModel):
    toxicity: float
    severe_toxicity: float
    obscene: float
    threat: float
    insult: float
    identity_attack: float
    risk_level: str  # safe | low | moderate | high
    assessment: str
    scan_id: Optional[int] = None

class HistoryResponse(BaseModel):
    items: List[dict]
    total: int

# ============== URL/IP CHECKER ==============

def detect_target_type(target: str) -> str:
    """Detect if target is URL or IP"""
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ip_pattern, target):
        return "ip"
    return "url"

@router.post("/url-check", response_model=URLCheckResponse)
async def check_url_or_ip(
    request: URLCheckRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Check URL or IP for security threats using VirusTotal"""
    target = request.target.strip()
    target_type = detect_target_type(target)
    
    try:
        from backend.ai_engine.our_ai_engine.tools import virustotal_scan
        result = virustotal_scan.invoke({"target": target})
        
        # Parse result properly
        is_safe = True
        risk_level = "safe"
        details = {"raw_result": result}
        malicious_count = 0
        suspicious_count = 0
        
        if isinstance(result, str):
            # Extract the actual counts from the VirusTotal response
            import re
            
            # Look for "Malicious: X" pattern
            malicious_match = re.search(r'Malicious:\s*(\d+)', result)
            suspicious_match = re.search(r'Suspicious:\s*(\d+)', result)
            
            if malicious_match:
                malicious_count = int(malicious_match.group(1))
            if suspicious_match:
                suspicious_count = int(suspicious_match.group(1))
            
            # Determine safety based on actual counts
            if malicious_count > 0:
                is_safe = False
                if malicious_count >= 5:
                    risk_level = "critical"
                elif malicious_count >= 3:
                    risk_level = "high"
                else:
                    risk_level = "medium"
            elif suspicious_count > 0:
                is_safe = False
                if suspicious_count >= 5:
                    risk_level = "medium"
                else:
                    risk_level = "low"
            else:
                is_safe = True
                risk_level = "safe"
            
            # Create a better summary
            if is_safe:
                summary = f"✅ This {target_type.upper()} appears to be safe. No security vendors flagged it as malicious."
            else:
                summary = f"⚠️ {malicious_count} vendor(s) flagged this as malicious, {suspicious_count} as suspicious."
            
            details["summary"] = summary
            details["malicious_count"] = malicious_count
            details["suspicious_count"] = suspicious_count
            details["virustotal_report"] = result
        
        # Save to history
        history = ToolHistory(
            user_id=current_user.id,
            tool_type="url_checker",
            input_data=target,
            output_data=result if isinstance(result, str) else str(result),
            extra_data={
                "target_type": target_type, 
                "risk_level": risk_level, 
                "is_safe": is_safe,
                "malicious_count": malicious_count,
                "suspicious_count": suspicious_count
            }
        )
        session.add(history)
        session.commit()
        session.refresh(history)
        
        return URLCheckResponse(
            target=target,
            target_type=target_type,
            is_safe=is_safe,
            risk_level=risk_level,
            details=details,
            scan_id=history.id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

# ============== CODE SNIPPET CHECKER ==============

SECURITY_PATTERNS = {
    "python": [
        {"pattern": r"\beval\s*\(", "name": "eval() usage", "severity": "high",
         "description": "eval() executes arbitrary code and is extremely dangerous with user input",
         "fix": "Use ast.literal_eval() for safe evaluation or avoid eval entirely"},
        {"pattern": r"\bexec\s*\(", "name": "exec() usage", "severity": "high",
         "description": "exec() executes arbitrary code strings",
         "fix": "Avoid exec() - use safer alternatives like function dispatch"},
        {"pattern": r"password\s*=\s*['\"][^'\"]+['\"]", "name": "Hardcoded password", "severity": "critical",
         "description": "Passwords should never be hardcoded in source code",
         "fix": "Use environment variables: os.getenv('PASSWORD')"},
        {"pattern": r"api_key\s*=\s*['\"][^'\"]+['\"]", "name": "Hardcoded API key", "severity": "critical",
         "description": "API keys should never be hardcoded",
         "fix": "Use environment variables: os.getenv('API_KEY')"},
        {"pattern": r"secret\s*=\s*['\"][^'\"]+['\"]", "name": "Hardcoded secret", "severity": "critical",
         "description": "Secrets should never be hardcoded",
         "fix": "Use environment variables or secret management"},
        {"pattern": r"SELECT.*\+.*user|SELECT.*%.*user|SELECT.*\.format\(", "name": "SQL Injection risk", "severity": "critical",
         "description": "String concatenation in SQL queries allows injection attacks",
         "fix": "Use parameterized queries: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"},
        {"pattern": r"subprocess\.call\([^,]+shell\s*=\s*True", "name": "Shell injection risk", "severity": "high",
         "description": "shell=True with user input allows command injection",
         "fix": "Use shell=False and pass arguments as list"},
        {"pattern": r"pickle\.loads?\(", "name": "Insecure deserialization", "severity": "high",
         "description": "pickle can execute arbitrary code during deserialization",
         "fix": "Use JSON or other safe serialization formats"},
        {"pattern": r"input\s*\(\s*\)", "name": "Unvalidated input", "severity": "low",
         "description": "User input should be validated before use",
         "fix": "Always validate and sanitize user input"},
        {"pattern": r"md5\(|sha1\(", "name": "Weak hashing algorithm", "severity": "medium",
         "description": "MD5 and SHA1 are cryptographically weak",
         "fix": "Use SHA-256 or bcrypt for passwords"},
    ],
    "javascript": [
        {"pattern": r"\beval\s*\(", "name": "eval() usage", "severity": "high",
         "description": "eval() executes arbitrary code",
         "fix": "Use JSON.parse() for JSON or Function constructor carefully"},
        {"pattern": r"innerHTML\s*=", "name": "innerHTML XSS risk", "severity": "high",
         "description": "innerHTML can execute malicious scripts",
         "fix": "Use textContent or sanitize HTML with DOMPurify"},
        {"pattern": r"document\.write\s*\(", "name": "document.write usage", "severity": "medium",
         "description": "document.write can be exploited for XSS",
         "fix": "Use DOM manipulation methods instead"},
        {"pattern": r"password\s*[=:]\s*['\"][^'\"]+['\"]", "name": "Hardcoded password", "severity": "critical",
         "description": "Passwords should never be in client-side code",
         "fix": "Use environment variables on server side"},
        {"pattern": r"localStorage\.setItem\([^,]+password", "name": "Password in localStorage", "severity": "critical",
         "description": "Storing passwords in localStorage is insecure",
         "fix": "Use secure HTTP-only cookies for auth tokens"},
    ],
}

@router.post("/code-check", response_model=CodeCheckResponse)
async def check_code_security(
    request: CodeCheckRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Analyze code snippet for security vulnerabilities"""
    code = request.code
    language = request.language.lower()
    
    patterns = SECURITY_PATTERNS.get(language, SECURITY_PATTERNS["python"])
    vulnerabilities = []
    
    for pattern_info in patterns:
        matches = re.finditer(pattern_info["pattern"], code, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            # Find line number
            line_num = code[:match.start()].count('\n') + 1
            vulnerabilities.append({
                "name": pattern_info["name"],
                "severity": pattern_info["severity"],
                "description": pattern_info["description"],
                "fix": pattern_info["fix"],
                "line": line_num,
                "code_snippet": match.group(0)[:50]
            })
    
    # Calculate risk level
    severity_scores = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    if not vulnerabilities:
        risk_level = "safe"
    else:
        max_severity = max(v["severity"] for v in vulnerabilities)
        risk_level = max_severity
    
    suggestions = list(set(v["fix"] for v in vulnerabilities))
    
    # Save to history
    history = ToolHistory(
        user_id=current_user.id,
        tool_type="code_checker",
        input_data=code[:1000],  # Limit stored code
        output_data=str({"total": len(vulnerabilities), "risk": risk_level}),
        extra_data={"language": language, "vulnerabilities": vulnerabilities[:10]}
    )
    session.add(history)
    session.commit()
    session.refresh(history)
    
    return CodeCheckResponse(
        vulnerabilities=vulnerabilities,
        risk_level=risk_level,
        total_issues=len(vulnerabilities),
        suggestions=suggestions,
        scan_id=history.id
    )

# ============== FAKE NEWS DETECTOR ==============

def analyze_with_ml_model(text: str) -> dict:
    """Use the ML model for fake news detection"""
    try:
        # Import the ML model analysis
        import sys
        fake_news_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fake_news", "script")
        if fake_news_dir not in sys.path:
            sys.path.insert(0, fake_news_dir)
        
        from full_analyse import analyze_news
        result = analyze_news(text)
        return result
    except Exception as e:
        print(f"ML model error: {e}")
        return None

@router.post("/fake-news-check", response_model=FakeNewsResponse)
async def check_fake_news(
    request: FakeNewsRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Analyze content for fake news using ML model"""
    content = request.content
    
    # Try ML model first
    ml_result = analyze_with_ml_model(content)
    
    if ml_result:
        # Use ML model results
        veracity = ml_result['veracity_label']
        confidence = ml_result['confidence_score']
        
        # Map veracity to verdict
        if veracity.lower() == "fake":
            verdict = "likely_fake"
        elif veracity.lower() == "real":
            verdict = "likely_real"
        else:
            verdict = "uncertain"
        
        # Extract red flags from emotion and manipulation analysis
        red_flags = []
        emotions = ml_result.get('emotion_scores', {})
        if emotions.get('fear', 0) > 0.4:
            red_flags.append("High fear-inducing language detected")
        if emotions.get('anger', 0) > 0.4:
            red_flags.append("Anger-driven expressions present")
        if emotions.get('urgency', 0) > 0.4:
            red_flags.append("Urgent or alarmist framing")
        
        manipulation = ml_result.get('political_bias_indicator', {})
        if manipulation.get('manipulation_level') != "Low":
            red_flags.append(f"{manipulation.get('manipulation_level')} political manipulation")
        
        analysis = ml_result.get('explanation', '')
        
    else:
        # Fallback to pattern-based detection
        red_flags = []
        total_weight = 0
        
        FAKE_NEWS_INDICATORS = [
            {"pattern": r"BREAKING|SHOCKING|YOU WON'T BELIEVE", "flag": "Sensationalist headline", "weight": 2},
            {"pattern": r"100%|guaranteed|proven", "flag": "Absolute claims without evidence", "weight": 1.5},
            {"pattern": r"share before.*deleted|they don't want you to know", "flag": "Urgency/conspiracy language", "weight": 2},
            {"pattern": r"scientists hate|doctors hate|one weird trick", "flag": "Clickbait patterns", "weight": 2},
            {"pattern": r"exposed|exposed!|exposed:", "flag": "Exposé language", "weight": 1},
            {"pattern": r"forward to \d+ people|share with \d+ friends", "flag": "Chain message pattern", "weight": 2.5},
            {"pattern": r"government hiding|media won't tell", "flag": "Anti-establishment rhetoric", "weight": 1.5},
            {"pattern": r"miracle cure|instant results|secret formula", "flag": "Too-good-to-be-true claims", "weight": 2},
            {"pattern": r"!!+|\?\?+|\.\.\.+", "flag": "Excessive punctuation", "weight": 0.5},
            {"pattern": r"[A-Z]{5,}", "flag": "Excessive caps (shouting)", "weight": 0.5},
        ]
        
        for indicator in FAKE_NEWS_INDICATORS:
            if re.search(indicator["pattern"], content, re.IGNORECASE):
                red_flags.append(indicator["flag"])
                total_weight += indicator["weight"]
        
        # Calculate verdict
        if total_weight >= 5:
            verdict = "likely_fake"
            confidence = min(0.95, 0.5 + total_weight * 0.08)
        elif total_weight >= 2:
            verdict = "uncertain"
            confidence = 0.5 + total_weight * 0.05
        else:
            verdict = "likely_real"
            confidence = max(0.6, 0.9 - total_weight * 0.1)
        
        # Generate analysis
        if verdict == "likely_fake":
            analysis = f"This content shows {len(red_flags)} warning signs commonly found in misinformation. Exercise caution and verify from trusted sources."
        elif verdict == "uncertain":
            analysis = f"This content has some concerning patterns. We recommend cross-checking with reliable news sources before sharing."
        else:
            analysis = "This content doesn't show obvious signs of misinformation, but always verify important claims from multiple sources."
    
    # Save to history
    history = ToolHistory(
        user_id=current_user.id,
        tool_type="fake_news",
        input_data=content[:500],
        output_data=verdict,
        extra_data={"red_flags": red_flags, "confidence": confidence if 'confidence' in locals() else ml_result.get('confidence_score', 0.5) if ml_result else 0.5}
    )
    session.add(history)
    session.commit()
    session.refresh(history)
    
    return FakeNewsResponse(
        content=content[:200] + "..." if len(content) > 200 else content,
        verdict=verdict,
        confidence=round(confidence if 'confidence' in locals() else ml_result.get('confidence_score', 0.5) if ml_result else 0.5, 2),
        red_flags=red_flags,
        analysis=analysis,
        scan_id=history.id
    )

# ============== QUIZ MODE ==============

QUIZ_QUESTIONS = {
    "phishing": [
        {"id": 1, "question": "You receive an email from 'support@amaz0n.com' asking you to verify your account. What should you do?",
         "options": ["Click the link and verify", "Reply with your details", "Ignore and report as phishing", "Forward to friends"],
         "correct": 2, "explanation": "The domain 'amaz0n.com' uses a zero instead of 'o' - a classic phishing technique."},
        {"id": 2, "question": "Which of these is a red flag in a phishing email?",
         "options": ["Company logo present", "Urgent action required", "Sent during business hours", "Has unsubscribe link"],
         "correct": 1, "explanation": "Urgency is a common manipulation tactic in phishing to prevent you from thinking carefully."},
        {"id": 3, "question": "A message says 'Your SBI account will be blocked in 24 hours. Click here to verify KYC.' What type of attack is this?",
         "options": ["Malware", "Phishing", "DDoS", "Man-in-the-middle"],
         "correct": 1, "explanation": "This is phishing - using fear and urgency to trick you into clicking malicious links."},
        {"id": 4, "question": "What should you check before clicking a link in an email?",
         "options": ["The sender's profile picture", "Hover over link to see actual URL", "The email subject line", "The time it was sent"],
         "correct": 1, "explanation": "Hovering reveals the actual destination URL which may differ from the displayed text."},
        {"id": 5, "question": "You get a WhatsApp message from an unknown number claiming to be your bank. They ask for your OTP. What do you do?",
         "options": ["Share OTP as they're from bank", "Ask them to prove identity first", "Never share OTP with anyone", "Call back the number"],
         "correct": 2, "explanation": "Banks NEVER ask for OTP. This is a social engineering attack."},
    ],
    "malware": [
        {"id": 6, "question": "What is ransomware?",
         "options": ["Software that speeds up your PC", "Malware that encrypts files and demands payment", "A type of antivirus", "A browser extension"],
         "correct": 1, "explanation": "Ransomware encrypts your files and demands payment (ransom) for the decryption key."},
        {"id": 7, "question": "Which file type is most likely to contain malware?",
         "options": [".txt", ".jpg", ".exe", ".pdf"],
         "correct": 2, "explanation": ".exe files are executable programs that can run malicious code directly."},
        {"id": 8, "question": "Your computer suddenly shows many pop-ups and runs slowly. What might this indicate?",
         "options": ["Normal behavior", "Malware infection", "Software update needed", "Low battery"],
         "correct": 1, "explanation": "Unexpected pop-ups and slowdowns are common symptoms of malware infection."},
        {"id": 9, "question": "What is a Trojan horse in cybersecurity?",
         "options": ["A strong password", "Malware disguised as legitimate software", "A type of firewall", "An encryption method"],
         "correct": 1, "explanation": "Like the Greek myth, a Trojan appears harmless but contains hidden malicious code."},
        {"id": 10, "question": "How can you protect against malware?",
         "options": ["Download from any website", "Disable antivirus for speed", "Keep software updated and use antivirus", "Open all email attachments"],
         "correct": 2, "explanation": "Regular updates patch vulnerabilities, and antivirus detects known threats."},
    ],
    "social_engineering": [
        {"id": 11, "question": "Someone calls claiming to be IT support and asks for your password. What should you do?",
         "options": ["Give password to help them", "Hang up and verify through official channels", "Ask them to email you", "Share only part of password"],
         "correct": 1, "explanation": "Legitimate IT never asks for passwords. Always verify through known official contacts."},
        {"id": 12, "question": "What is 'pretexting' in social engineering?",
         "options": ["Writing code", "Creating a fake scenario to gain trust", "Sending spam", "Installing software"],
         "correct": 1, "explanation": "Pretexting involves creating a fabricated scenario to manipulate victims into sharing information."},
        {"id": 13, "question": "A stranger at a coffee shop asks to use your phone 'for an emergency'. What's the risk?",
         "options": ["No risk at all", "They might install malware or access data", "They'll return it safely", "It's always safe to help"],
         "correct": 1, "explanation": "Physical access to your device can allow data theft or malware installation."},
        {"id": 14, "question": "What is 'tailgating' in security?",
         "options": ["Following someone into a secure area without authorization", "Sending follow-up emails", "Tracking website visitors", "A type of encryption"],
         "correct": 0, "explanation": "Tailgating is physically following authorized personnel into restricted areas."},
        {"id": 15, "question": "You find a USB drive in the parking lot. What should you do?",
         "options": ["Plug it in to find the owner", "Give it to security/IT", "Keep it", "Throw it away"],
         "correct": 1, "explanation": "Unknown USB drives may contain malware. Let IT handle it safely."},
    ],
    "upi_fraud": [
        {"id": 16, "question": "Someone sends you a 'collect request' on UPI saying it's a refund. What happens if you approve?",
         "options": ["You receive money", "Money is deducted from your account", "Nothing happens", "Your UPI gets blocked"],
         "correct": 1, "explanation": "Collect requests TAKE money from you. Scammers trick people by calling it a 'refund'."},
        {"id": 17, "question": "A seller asks you to scan a QR code to 'receive' payment. Is this legitimate?",
         "options": ["Yes, QR codes can receive money", "No, scanning QR codes only sends money", "Depends on the app", "Only works for small amounts"],
         "correct": 1, "explanation": "Scanning QR codes initiates PAYMENT. You cannot receive money by scanning."},
        {"id": 18, "question": "What should you NEVER share with anyone regarding UPI?",
         "options": ["Your UPI ID", "Your bank name", "Your UPI PIN and OTP", "Your phone number"],
         "correct": 2, "explanation": "UPI PIN and OTP are like your ATM PIN - never share them with anyone."},
        {"id": 19, "question": "Someone asks you to download AnyDesk/TeamViewer to help with a 'refund'. What is this?",
         "options": ["Legitimate customer support", "A screen sharing scam", "A faster refund method", "Bank's official process"],
         "correct": 1, "explanation": "Scammers use screen sharing apps to see your screen and steal banking credentials."},
        {"id": 20, "question": "You receive ₹1 from an unknown person and they ask you to return ₹10,000 'sent by mistake'. What should you do?",
         "options": ["Return the money immediately", "Ignore and block", "Report to cyber cell", "Both B and C"],
         "correct": 3, "explanation": "This is a common scam. Block the person and report to cybercrime.gov.in"},
    ],
    "cyber_laws": [
        {"id": 21, "question": "Under which section of IT Act is identity theft punishable in India?",
         "options": ["Section 43", "Section 66C", "Section 67", "Section 72"],
         "correct": 1, "explanation": "Section 66C of IT Act deals with identity theft with up to 3 years imprisonment."},
        {"id": 22, "question": "What is the national cybercrime helpline number in India?",
         "options": ["100", "112", "1930", "181"],
         "correct": 2, "explanation": "1930 is the 24/7 national cybercrime helpline for reporting cyber fraud."},
        {"id": 23, "question": "Where can you report cybercrime online in India?",
         "options": ["facebook.com", "cybercrime.gov.in", "google.com", "police.gov.in"],
         "correct": 1, "explanation": "cybercrime.gov.in is the official National Cyber Crime Reporting Portal."},
        {"id": 24, "question": "Within how many days should you report bank fraud for full refund eligibility?",
         "options": ["1 day", "3 days", "7 days", "30 days"],
         "correct": 1, "explanation": "Report within 3 days for zero liability. Delay reduces refund eligibility."},
        {"id": 25, "question": "Which organization handles cyber security incidents in India?",
         "options": ["CBI", "CERT-In", "RAW", "NIA"],
         "correct": 1, "explanation": "CERT-In (Indian Computer Emergency Response Team) handles cybersecurity incidents."},
    ],
}

def get_quiz_questions(category: str, num_questions: int) -> List[dict]:
    """Get random questions for quiz - fallback to static questions"""
    if category == "mixed":
        all_questions = []
        for cat_questions in QUIZ_QUESTIONS.values():
            all_questions.extend(cat_questions)
    else:
        all_questions = QUIZ_QUESTIONS.get(category, [])
    
    if not all_questions:
        return []
    
    selected = random.sample(all_questions, min(num_questions, len(all_questions)))
    # Remove correct answer and explanation for client
    return [{"id": q["id"], "question": q["question"], "options": q["options"], "category": category} for q in selected]


async def generate_ai_quiz_questions(category: str, num_questions: int) -> List[dict]:
    """Generate unique quiz questions using Gemini AI"""
    import json
    
    try:
        from google import genai
        from google.genai import types
        
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        
        client = genai.Client(api_key=api_key)
        
        category_descriptions = {
            "phishing": "phishing attacks, email scams, fake websites, social engineering via email/SMS, identifying suspicious links and messages",
            "malware": "malware types (virus, trojan, ransomware, spyware), infection symptoms, protection methods, safe downloading practices",
            "social_engineering": "social engineering tactics, pretexting, baiting, tailgating, vishing, manipulation techniques, human psychology in security",
            "upi_fraud": "UPI payment frauds in India, QR code scams, collect request scams, fake refund calls, OTP theft, digital payment safety",
            "cyber_laws": "Indian cyber laws, IT Act sections, cybercrime reporting (1930 helpline, cybercrime.gov.in), CERT-In, legal rights and penalties",
            "mixed": "all cybersecurity topics including phishing, malware, social engineering, UPI fraud, and Indian cyber laws"
        }
        
        topic = category_descriptions.get(category, category_descriptions["mixed"])
        
        prompt = f"""Generate {num_questions} unique multiple-choice quiz questions about {topic}.

IMPORTANT RULES:
1. Questions must be practical and scenario-based (not just definitions)
2. Include India-specific context where relevant (UPI, Aadhaar, Indian banks, 1930 helpline, etc.)
3. Each question must have exactly 4 options
4. Only ONE option should be correct
5. Make questions challenging but fair
6. Include real-world scenarios people might encounter
7. Vary difficulty levels

Return ONLY a valid JSON array with this exact structure (no markdown, no explanation):
[
  {{
    "question": "Your question here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct": 0,
    "explanation": "Brief explanation why this answer is correct"
  }}
]

The "correct" field is the index (0-3) of the correct option.
Generate exactly {num_questions} questions. Return ONLY the JSON array, nothing else."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.9,  # Higher for more variety
                max_output_tokens=4096
            )
        )
        
        # Parse the response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        questions = json.loads(response_text)
        
        # Validate and format questions
        formatted_questions = []
        for i, q in enumerate(questions):
            if all(key in q for key in ["question", "options", "correct", "explanation"]):
                if len(q["options"]) == 4 and 0 <= q["correct"] <= 3:
                    formatted_questions.append({
                        "id": 1000 + i,  # AI-generated IDs start from 1000
                        "question": q["question"],
                        "options": q["options"],
                        "correct": q["correct"],
                        "explanation": q["explanation"],
                        "category": category,
                        "ai_generated": True
                    })
        
        if len(formatted_questions) >= num_questions // 2:  # At least half successful
            return formatted_questions[:num_questions]
        
        return None
        
    except Exception as e:
        print(f"❌ AI Quiz generation error: {e}")
        import traceback
        traceback.print_exc()
        return None


# Store AI-generated questions temporarily for answer validation
_ai_quiz_cache = {}

@router.post("/quiz/start")
async def start_quiz(
    request: QuizStartRequest,
    current_user: User = Depends(get_current_user)
):
    """Start a new quiz session with AI-generated questions"""
    
    # Try AI generation first
    ai_questions = await generate_ai_quiz_questions(request.category, request.num_questions)
    
    if ai_questions and len(ai_questions) > 0:
        # Store full questions in cache for validation
        quiz_id = f"{current_user.id}_{datetime.now().timestamp()}"
        _ai_quiz_cache[quiz_id] = {q["id"]: q for q in ai_questions}
        
        # Return questions without correct answers
        client_questions = [
            {"id": q["id"], "question": q["question"], "options": q["options"], "category": q["category"]}
            for q in ai_questions
        ]
        
        return {
            "questions": client_questions, 
            "total": len(client_questions), 
            "category": request.category,
            "quiz_id": quiz_id,
            "ai_generated": True
        }
    
    # Fallback to static questions
    questions = get_quiz_questions(request.category, request.num_questions)
    if not questions:
        raise HTTPException(status_code=400, detail="No questions available for this category")
    
    return {"questions": questions, "total": len(questions), "category": request.category, "ai_generated": False}

@router.post("/quiz/submit")
async def submit_quiz(
    request: QuizSubmitRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Submit quiz answers and get results"""
    
    # Check if this is an AI-generated quiz
    ai_questions = None
    if request.quiz_id and request.quiz_id in _ai_quiz_cache:
        ai_questions = _ai_quiz_cache[request.quiz_id]
    
    # Build answer lookup from static questions
    static_questions = {}
    for cat, questions in QUIZ_QUESTIONS.items():
        for q in questions:
            static_questions[q["id"]] = q
    
    results = []
    correct_count = 0
    category = "mixed"
    
    for answer in request.answers:
        q_id = answer.get("question_id")
        selected = answer.get("selected")
        
        # Check AI questions first (IDs >= 1000), then static questions
        question = None
        if ai_questions and q_id in ai_questions:
            question = ai_questions[q_id]
        elif q_id in static_questions:
            question = static_questions[q_id]
        
        if not question:
            continue
        
        is_correct = selected == question["correct"]
        if is_correct:
            correct_count += 1
        
        # Get category from question
        if "category" in question:
            category = question["category"]
        
        results.append({
            "question_id": q_id,
            "question": question["question"],
            "selected": selected,
            "correct": question["correct"],
            "is_correct": is_correct,
            "explanation": question.get("explanation", ""),
            "correct_answer": question["options"][question["correct"]]
        })
    
    total = len(request.answers)
    score_pct = (correct_count / total * 100) if total > 0 else 0
    
    # Clean up AI quiz cache after submission
    if request.quiz_id and request.quiz_id in _ai_quiz_cache:
        del _ai_quiz_cache[request.quiz_id]
    
    # Save attempt
    attempt = QuizAttempt(
        user_id=current_user.id,
        quiz_category=category,
        total_questions=total,
        correct_answers=correct_count,
        score_percentage=score_pct,
        answers=results,
        time_taken_seconds=request.time_taken_seconds
    )
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    
    return {
        "attempt_id": attempt.id,
        "total_questions": total,
        "correct_answers": correct_count,
        "score_percentage": round(score_pct, 1),
        "results": results,
        "time_taken": request.time_taken_seconds,
        "ai_generated": ai_questions is not None
    }

# ============== HISTORY ENDPOINTS ==============

@router.get("/history/{tool_type}")
async def get_tool_history(
    tool_type: str,
    limit: int = 20,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get history for a specific tool"""
    statement = select(ToolHistory).where(
        ToolHistory.user_id == current_user.id,
        ToolHistory.tool_type == tool_type
    ).order_by(ToolHistory.created_at.desc()).limit(limit)
    
    items = session.exec(statement).all()
    
    return {
        "items": [
            {
                "id": item.id,
                "input": item.input_data,
                "output": item.output_data,
                "extra_data": item.extra_data,
                "created_at": item.created_at.isoformat()
            }
            for item in items
        ],
        "total": len(items)
    }

@router.get("/quiz/history")
async def get_quiz_history(
    limit: int = 20,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get quiz attempt history"""
    statement = select(QuizAttempt).where(
        QuizAttempt.user_id == current_user.id
    ).order_by(QuizAttempt.created_at.desc()).limit(limit)
    
    attempts = session.exec(statement).all()
    
    return {
        "attempts": [
            {
                "id": a.id,
                "category": a.quiz_category,
                "score": a.score_percentage,
                "correct": a.correct_answers,
                "total": a.total_questions,
                "time_taken": a.time_taken_seconds,
                "created_at": a.created_at.isoformat()
            }
            for a in attempts
        ],
        "total": len(attempts)
    }

@router.get("/quiz/categories")
async def get_quiz_categories():
    """Get available quiz categories"""
    return {
        "categories": [
            {"id": "mixed", "name": "Mixed Topics", "description": "Questions from all categories", "icon": "shuffle"},
            {"id": "phishing", "name": "Phishing Detection", "description": "Identify phishing attempts", "icon": "phishing"},
            {"id": "malware", "name": "Malware Awareness", "description": "Learn about malware threats", "icon": "bug_report"},
            {"id": "social_engineering", "name": "Social Engineering", "description": "Recognize manipulation tactics", "icon": "psychology"},
            {"id": "upi_fraud", "name": "UPI & Payment Fraud", "description": "Protect your digital payments", "icon": "currency_rupee"},
            {"id": "cyber_laws", "name": "Indian Cyber Laws", "description": "Know your rights and reporting", "icon": "gavel"},
        ]
    }


# ============== TOXICITY CHECKER ==============

@router.post("/toxicity-check", response_model=ToxicityCheckResponse)
async def check_toxicity(
    request: ToxicityCheckRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Analyze text for toxicity using Detoxify model"""
    text = request.text
    
    try:
        from detoxify import Detoxify
        
        # Initialize model
        model = Detoxify('original')
        
        # Get predictions
        results = model.predict(text)
        
        # Determine risk level
        max_score = max(results.values())
        max_category = max(results, key=results.get)
        
        if max_score > 0.7:
            risk_level = "high"
            assessment = f"⛔ HIGH RISK - This content shows high levels of {max_category.replace('_', ' ')} ({max_score:.1%}). This type of content may violate community guidelines and could be harmful."
        elif max_score > 0.5:
            risk_level = "moderate"
            assessment = f"⚠️ MODERATE RISK - This content contains moderate {max_category.replace('_', ' ')} ({max_score:.1%}). Consider reviewing and potentially moderating this content."
        elif max_score > 0.3:
            risk_level = "low"
            assessment = f"🟡 LOW RISK - This content has some indicators of {max_category.replace('_', ' ')} ({max_score:.1%}). Generally acceptable but may need context-based review."
        else:
            risk_level = "safe"
            assessment = "✅ SAFE - This content appears to be non-toxic and appropriate. No significant toxicity indicators detected."
        
        # Save to history
        history = ToolHistory(
            user_id=current_user.id,
            tool_type="toxicity_checker",
            input_data=text[:500],
            output_data=risk_level,
            extra_data={
                "risk_level": risk_level,
                "max_score": float(max_score),
                "max_category": max_category,
                "scores": {k: float(v) for k, v in results.items()}
            }
        )
        session.add(history)
        session.commit()
        session.refresh(history)
        
        return ToxicityCheckResponse(
            toxicity=float(results['toxicity']),
            severe_toxicity=float(results['severe_toxicity']),
            obscene=float(results['obscene']),
            threat=float(results['threat']),
            insult=float(results['insult']),
            identity_attack=float(results['identity_attack']),
            risk_level=risk_level,
            assessment=assessment,
            scan_id=history.id
        )
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="Detoxify library not installed. Run: pip install detoxify"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
