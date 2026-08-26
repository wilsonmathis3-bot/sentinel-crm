"""Caption drafter — Anthropic cheapest adequate model, DRAFT only.
Never auto-posts. Generates caption + hashtags from asset prompt + persona voice.
"""
import os
from typing import Dict, Any, Optional

# Use anthropic SDK if available; fallback to raw httpx
try:
    import anthropic
    ANTHROPIC_SDK = True
except ImportError:
    ANTHROPIC_SDK = False

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
# Cheapest adequate model per agent doctrine
CAPTION_MODEL = os.getenv("CAPTION_MODEL", "claude-3-haiku-20240307")


async def draft_caption(prompt: str, persona_voice: str, platform: str = "instagram") -> Dict[str, Any]:
    """Draft a caption and hashtags for an asset.
    
    Returns dict with caption, hashtags, cost_estimate.
    Pure LLM call — only for caption drafting, never for posting decisions.
    """
    if not ANTHROPIC_API_KEY:
        return {
            "status": "unconfigured",
            "caption": "",
            "hashtags": "",
            "cost_estimate": 0.0,
        }
    
    system_prompt = (
        f"You are a social media caption writer. Write in this voice: {persona_voice}. "
        "Keep captions under 150 words. Add 5-10 relevant hashtags. "
        "Return ONLY a JSON object with keys: caption, hashtags."
    )
    
    user_prompt = f"Write a caption for this content: {prompt}\nPlatform: {platform}"
    
    try:
        if ANTHROPIC_SDK:
            client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
            message = await client.messages.create(
                model=CAPTION_MODEL,
                max_tokens=300,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            content = message.content[0].text if message.content else ""
            # Rough cost estimate: Haiku ~$0.25/1M tokens input, ~$1.25/1M output
            input_tokens = message.usage.input_tokens if hasattr(message, "usage") else 0
            output_tokens = message.usage.output_tokens if hasattr(message, "usage") else 0
            cost = (input_tokens * 0.25 + output_tokens * 1.25) / 1_000_000
        else:
            # Raw httpx fallback
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": CAPTION_MODEL,
                        "max_tokens": 300,
                        "temperature": 0.7,
                        "system": system_prompt,
                        "messages": [{"role": "user", "content": user_prompt}],
                    }
                )
                resp.raise_for_status()
                data = resp.json()
                content = data["content"][0]["text"] if data.get("content") else ""
                usage = data.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                cost = (input_tokens * 0.25 + output_tokens * 1.25) / 1_000_000
        
        # Parse JSON from response (best effort)
        import json
        try:
            parsed = json.loads(content)
            caption = parsed.get("caption", content[:200])
            hashtags = parsed.get("hashtags", "")
        except json.JSONDecodeError:
            caption = content[:200]
            hashtags = ""
        
        return {
            "status": "ok",
            "caption": caption,
            "hashtags": hashtags,
            "cost_estimate": round(cost, 6),
            "model": CAPTION_MODEL,
        }
    
    except Exception as exc:
        return {
            "status": "error",
            "caption": "",
            "hashtags": "",
            "cost_estimate": 0.0,
            "error": str(exc),
        }
