# Simple but capable NLP utilities: category, sentiment, translate
from textblob import TextBlob
from googletrans import Translator

KEYWORDS = {
    "road": ["road", "pothole", "traffic", "asphalt", "street"],
    "garbage": ["garbage", "waste", "trash", "dump", "bins"],
    "water": ["water", "leak", "pipe", "drain", "sewer"],
    "electricity": ["electric", "power", "light", "streetlight", "transformer", "cable"],
}

translator = Translator()

def predict_category_text(text: str) -> str:
    text = (text or "").lower()
    scores = {k: 0 for k in KEYWORDS}
    for cat, words in KEYWORDS.items():
        for w in words:
            if w in text:
                scores[cat] += 1
    best = max(scores.items(), key=lambda x: x[1])
    return best[0] if best[1] > 0 else "general"

def analyze_sentiment(text: str) -> str:
    try:
        tb = TextBlob(text or "")
        polarity = tb.sentiment.polarity
        if polarity > 0.2:
            return "Positive"
        elif polarity < -0.2:
            return "Negative"
        else:
            return "Neutral"
    except Exception:
        return "Neutral"

def translate_text(text: str, dest: str = "en") -> str:
    if not text:
        return ""
    try:
        res = translator.translate(text, dest=dest)
        return res.text
    except Exception:
        # fallback: return original
        return text
