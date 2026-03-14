import json
import httpx
from config import settings
from models.report import PortfolioReport
from ai.prompts import build_analysis_prompt


GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
    "/{model}:generateContent?key={key}"
)

async def explain_report(report: PortfolioReport) -> tuple[str, str]:
    prompt = build_analysis_prompt(report)
    url = GEMINI_URL.format(model=settings.GEMINI_MODEL, key=settings.GEMINI_API_KEY)

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 10000,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

        raw = response.json()
        text = raw["candidates"][0]["content"]["parts"][0]["text"].strip()
        
        # Log raw response so you can see what Gemini actually returned
        print(f"[gemini] raw response: {text}")

        # Strip markdown fences
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        # Find the JSON object boundaries explicitly
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object found in response")
        text = text[start:end]

        parsed = json.loads(text)
        return (
            parsed.get("explanation", ""),
            parsed.get("recommendation_summary", ""),
        )

    except Exception as e:
        print(f"[gemini] failed: {type(e).__name__}: {e}")
        return "", ""