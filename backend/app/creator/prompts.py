"""Prompt engine — deterministic generator, zero LLM calls.
Persona brief_json × content pillars × format × trending-topic slots → N prompts.
"""
import json
import random
from typing import List, Dict, Any

# Deterministic format templates per platform/format
FORMAT_TEMPLATES = {
    "reel": "{hook} {scene}. {action}. {outro} #Reel #Content",
    "carousel": "{hook} {scene}. Swipe for {detail}. {outro}",
    "static": "{scene}. {mood}. {detail}.",
    "story": "{scene} — {mood}. Tap for {cta}.",
}

# Trending slot fillers (rotated weekly via seed)
TRENDING_SLOTS = [
    "golden hour", "behind the scenes", "day in the life", "transformation",
    "before/after", "POV", "aesthetic", "routine", "minimalist", "raw",
]


def _shuffle_weekly(items: List[str], week_seed: int) -> List[str]:
    """Deterministically shuffle items based on week number."""
    rng = random.Random(week_seed)
    shuffled = items[:]
    rng.shuffle(shuffled)
    return shuffled


def generate_prompts(persona_brief: Dict[str, Any], count: int = 20,
                      week_number: int = 1, formats: List[str] = None) -> List[Dict[str, Any]]:
    """Generate N deterministic prompts from persona brief.
    
    Args:
        persona_brief: parsed brief_json dict
        count: number of prompts to generate (default 20)
        week_number: ISO week number for deterministic trending slots
        formats: list of format keys to use (default all)
    
    Returns:
        List of prompt dicts: {prompt, format, pillar, trending_slot}
    """
    if formats is None:
        formats = list(FORMAT_TEMPLATES.keys())
    
    pillars = persona_brief.get("content_pillars", ["lifestyle"])
    dna = persona_brief.get("dna", "")
    look = persona_brief.get("look", "")
    voice = persona_brief.get("voice", "")
    niche = persona_brief.get("niche", "")
    
    # Weekly trending slots
    weekly_trends = _shuffle_weekly(TRENDING_SLOTS, week_number)
    
    prompts = []
    for i in range(count):
        pillar = pillars[i % len(pillars)]
        fmt = formats[i % len(formats)]
        trend = weekly_trends[i % len(weekly_trends)]
        
        # Build prompt from archetype DNA
        base = f"{dna}. {look}. {niche}."
        
        # Add pillar-specific scene
        scene = f"{pillar} scene, {trend} lighting"
        
        # Format-specific assembly
        template = FORMAT_TEMPLATES.get(fmt, FORMAT_TEMPLATES["static"])
        prompt_text = template.format(
            hook=f"{voice} moment:",
            scene=scene,
            action="candid capture",
            outro="quiet confidence",
            detail="the full story",
            mood="effortless",
            cta="more",
        )
        
        # Combine base + formatted prompt
        full_prompt = f"{base} {prompt_text} Photorealistic, high detail, studio quality."
        
        prompts.append({
            "prompt": full_prompt,
            "format": fmt,
            "pillar": pillar,
            "trending_slot": trend,
            "week_number": week_number,
        })
    
    return prompts
