from fastapi import FastAPI
from pydantic import BaseModel
from full_analyse import analyze_news

app = FastAPI(
    title="Fake News & Political Bias Analyzer",
    description="Text-based fake news detection and political manipulation analysis",
    version="1.0"
)

# -----------------------------
# Request schema
# -----------------------------
class NewsRequest(BaseModel):
    text: str
    source: str | None = None


# -----------------------------
# API endpoint
# -----------------------------
@app.post("/analyze")
def analyze(request: NewsRequest):
    return analyze_news(
        text=request.text,
        source=request.source
    )


# -----------------------------
# Health check
# -----------------------------
@app.get("/")
def root():
    return {"status": "API is running"}
