"""Weekly batch job — Sunday 21:00 PT.
Generates prompts per persona, fires Leonardo generations, drafts captions.
Handles failures gracefully (mark job failed, continue).
"""
import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List

from sqlalchemy.orm import Session
from app import models
from app.creator.leonardo import LeonardoClient
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
    
    leonardo_ids = []
    credits_used = 0.0
    failed_prompts = []
    
    try:
        for spec in prompt_specs:
            try:
                # Fire Leonardo generation
                result = await LeonardoClient.create_generation(
                    prompt=spec["prompt"],
                    num_images=1,
                    model_id=persona.leonardo_model_id or os.getenv("LEONARDO_MODEL_ID"),
                )
                gen_id = result.get("sdGenerationJob", {}).get("generationId")
                
                if gen_id:
                    leonardo_ids.append(gen_id)
                    credits_used += 1.0  # stub; real cost from poll
                    
                    # Draft caption
                    voice = brief.get("voice", "")
                    caption_result = await draft_caption(spec["prompt"], voice)
                    
                    # Create asset record
                    asset = models.CreatorAsset(
                        persona_id=persona.id,
                        kind=models.AssetKind.CONTENT,
                        leonardo_generation_id=gen_id,
                        prompt=spec["prompt"],
                        caption_draft=caption_result.get("caption", ""),
                        credits_used=1.0,
                        status=models.AssetApproval.PENDING,
                    )
                    db.add(asset)
            except Exception as exc:
                failed_prompts.append({"prompt": spec["prompt"], "error": str(exc)})
                # Continue to next prompt — don't crash the batch
                continue
        
        # Update job
        job.leonardo_ids_json = json.dumps({
            "ids": leonardo_ids,
            "failed": failed_prompts,
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
            "leonardo_ids": len(leonardo_ids),
            "failed": len(failed_prompts),
            "credits_used": credits_used,
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
