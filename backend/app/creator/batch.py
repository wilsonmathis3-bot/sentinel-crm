"""Weekly batch job — Sunday 21:00 PT.
Generates prompts per persona, fires image generation via provider layer,
drafts captions. Handles failures gracefully (mark job failed, continue).

Migration lesson: imports must come before module-level constants so
alembic/model loading doesn't crash on env reads.
"""
import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from app import models
from app.creator.providers import generate_with_fallback, get_provider, DEFAULT_IMAGE_PROVIDER
from app.creator.prompts import generate_prompts
from app.creator.captions import draft_caption

WEEKLY_PROMPT_COUNT = int(os.getenv("WEEKLY_PROMPT_COUNT", "20"))
ASSETS_BASE_PATH = os.getenv("CREATOR_ASSETS_PATH", "/app/backend/creator_assets")


async def run_weekly_batch(db: Session, week_number: int = None) -> Dict[str, Any]:
    """Run the weekly content generation batch for all incubating personas.
    
    Args:
        db: SQLAlchemy session
        week_number: ISO week number (default: current week)
    
    Returns:
        Summary dict with per-persona results and total credits used.
    """
    if week_number is None:
        week_number = datetime.now(timezone.utc).isocalendar()[1]
    
    # Get all incubating personas
    personas = db.query(models.Persona).filter(
        models.Persona.lifecycle == models.PersonaLifecycle.INCUBATING
    ).all()
    
    if not personas:
        return {"status": "no_personas", "message": "No incubating personas found"}
    
    results = []
    total_credits = 0.0
    
    for persona in personas:
        persona_result = await _generate_for_persona(db, persona, week_number)
        results.append(persona_result)
        total_credits += persona_result.get("credits_used", 0.0)
    
    return {
        "status": "ok",
        "week_number": week_number,
        "personas_processed": len(personas),
        "total_credits_used": round(total_credits, 2),
        "results": results,
    }


async def _generate_for_persona(db: Session, persona: models.Persona,
                                 week_number: int) -> Dict[str, Any]:
    """Generate content batch for a single persona."""
    # Parse brief
    brief = {}
    try:
        brief = json.loads(persona.brief_json or "{}")
    except Exception:
        pass

    # Generate prompts deterministically
    prompt_specs = generate_prompts(
        persona_brief=brief,
        count=WEEKLY_PROMPT_COUNT,
        week_number=week_number,
    )

    # Create job record
    job = models.GenerationJob(
        persona_id=persona.id,
        purpose=models.JobPurpose.CONTENT_BATCH,
        status=models.JobStatus.RUNNING,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    gen_ids = []
    credits_used = 0.0
    failed_prompts = []
    provider_log = []  # [{provider, cost, fallback_used}]

    try:
        for spec in prompt_specs:
            try:
                # Use provider layer with fallback (Pollinations -> Perchance)
                result = await generate_with_fallback(
                    prompt=spec["prompt"],
                    width=1024,
                    height=1024,
                    primary=os.getenv("IMAGE_PROVIDER", DEFAULT_IMAGE_PROVIDER),
                    fallback="perchance",
                )

                image_path = result.get("image_url")
                provider = result.get("provider", "unknown")
                cost = result.get("cost", 0.0)
                fallback_used = result.get("fallback_used", False)

                gen_ids.append({
                    "provider": provider,
                    "path": image_path,
                    "fallback": fallback_used,
                })
                credits_used += cost
                provider_log.append({
                    "provider": provider,
                    "cost": cost,
                    "fallback": fallback_used,
                })

                # Draft caption
                voice = brief.get("voice", "")
                caption_result = await draft_caption(spec["prompt"], voice)

                # Create asset record — log provider in existing leonardo_generation_id
                # column as JSON when non-Leonardo (migration lesson: no new cols without ALTER)
                asset_meta = json.dumps({
                    "provider": provider,
                    "path": image_path,
                    "fallback": fallback_used,
                })

                asset = models.CreatorAsset(
                    persona_id=persona.id,
                    kind=models.AssetKind.CONTENT,
                    leonardo_generation_id=asset_meta,  # overloaded for provider tracking
                    file_path=image_path,
                    prompt=spec["prompt"],
                    caption_draft=caption_result.get("caption", ""),
                    credits_used=cost,
                    status=models.AssetApproval.PENDING,
                )
                db.add(asset)
            except Exception as exc:
                failed_prompts.append({"prompt": spec["prompt"], "error": str(exc)})
                # Continue to next prompt — don't crash the batch
                continue

        # Update job — log provider info in existing leonardo_ids_json column
        job.leonardo_ids_json = json.dumps({
            "ids": gen_ids,
            "failed": failed_prompts,
            "providers": provider_log,
            "total_cost": credits_used,
        })
        job.credits_used = credits_used
        job.status = models.JobStatus.COMPLETED if not failed_prompts else models.JobStatus.COMPLETED
        job.finished_at = datetime.now(timezone.utc)

        db.commit()

        return {
            "persona_id": persona.id,
            "persona_name": persona.name,
            "status": "ok",
            "prompts_generated": len(prompt_specs),
            "images_generated": len(gen_ids),
            "failed": len(failed_prompts),
            "credits_used": credits_used,
            "providers": list({p["provider"] for p in provider_log}),
        }

    except Exception as exc:
        job.status = models.JobStatus.FAILED
        job.leonardo_ids_json = json.dumps({"error": str(exc)})
        db.commit()

        return {
            "persona_id": persona.id,
            "persona_name": persona.name,
            "status": "failed",
            "error": str(exc),
            "credits_used": credits_used,
        }
