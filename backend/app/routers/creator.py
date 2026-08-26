"""Creator Studio router — Phase A.
Prefix: /api/creator
All endpoints behind get_current_active_user.
"""
import os
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_active_user
from app import models, schemas
from app.creator.leonardo import LeonardoClient

router = APIRouter()

# ---------------------------------------------------------------------------
# Seed data — three locked personas
# ---------------------------------------------------------------------------
PERSONA_SEEDS = [
    {
        "name": "Nova Reyes",
        "slug": "nova-reyes",
        "archetype": "runway-athlete",
        "brief_json": json.dumps({
            "dna": "high-fashion editorial x fitness discipline",
            "look": "late-20s, statuesque, olive skin, dark slicked hair, sharp jawline, minimal makeup, neutral-toned athletic-luxury wardrobe",
            "niche": "discipline aesthetics — 5am training, clean eating, quiet luxury, travel between shoots",
            "content_pillars": ["morning routine reels", "gym-form clips", "capsule-wardrobe stills", "city-window portraits"],
            "voice": "calm, clipped, motivational without hype",
            "platform_fit": ["Instagram", "TikTok"],
            "monetization": "athleisure/loungewear affiliate → activewear brand deals → own capsule line",
        }),
    },
    {
        "name": "Milo Kane",
        "slug": "milo-kane",
        "archetype": "tech-genius",
        "brief_json": json.dumps({
            "dna": "tech-founder charisma x skater accessibility",
            "look": "mid-20s, lean, light stubble, tousled brown hair, vintage tees + overshirts, film-grain photo treatment",
            "niche": "build in public lifestyle — gadgets, coffee shops, late-night coding, street spots, honest takes on tech",
            "content_pillars": ["desk-setup stills", "gadget first-looks", "skate-line clips", "what I learned this week carousels"],
            "voice": "witty, self-deprecating, curious",
            "platform_fit": ["TikTok", "YouTube Shorts", "X"],
            "monetization": "gadget affiliates → tech brand sponsorships → own product drops",
        }),
    },
    {
        "name": "Sable Moreau",
        "slug": "sable-moreau",
        "archetype": "art-world globetrotter",
        "brief_json": json.dumps({
            "dna": "art-world muse x globe-trotter",
            "look": "early-30s, androgynous-elegant, copper skin, cropped platinum curls, sculptural jewelry, architectural backdrops",
            "niche": "slow luxury travel + contemporary art — gallery openings, boutique hotels, coastal towns, design objects",
            "content_pillars": ["destination postcards", "room tours", "art-mention captions", "golden-hour portraits"],
            "voice": "sparse, poetic, insider",
            "platform_fit": ["Instagram", "Pinterest"],
            "monetization": "hotel/tourism board partnerships → gallery/brand collabs → curated travel guides",
        }),
    },
]

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------
class PersonaOut(BaseModel):
    id: int
    name: str
    slug: str
    archetype: Optional[str]
    status: str
    leonardo_model_id: Optional[str]
    brief_json: Optional[str] = None
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

class PersonaCreate(BaseModel):
    name: str
    slug: str
    archetype: Optional[str] = None
    brief_json: Optional[str] = None

class AssetOut(BaseModel):
    id: int
    persona_id: int
    kind: str
    leonardo_generation_id: Optional[str]
    file_path: Optional[str]
    prompt: Optional[str]
    credits_used: float
    status: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

class JobOut(BaseModel):
    id: int
    persona_id: int
    purpose: str
    status: str
    leonardo_ids_json: Optional[str]
    credits_used: float
    created_at: Optional[datetime]
    finished_at: Optional[str]

    class Config:
        from_attributes = True

class CanonizeRequest(BaseModel):
    asset_ids: List[int]

class TrainResponse(BaseModel):
    status: str
    message: str
    job_id: Optional[int] = None

# ---------------------------------------------------------------------------
# Seed helper
# ---------------------------------------------------------------------------
def _seed_personas(db: Session):
    """Insert the three personas if table is empty."""
    if db.query(models.Persona).first():
        return
    for p in PERSONA_SEEDS:
        db.add(models.Persona(**p))
    db.commit()

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/leonardo-balance")
async def leonardo_balance():
    """Account balances: API credit vs web tokens (proxied, auth-gated)."""
    from app.creator.leonardo import LeonardoClient
    if not LeonardoClient.configured():
        raise HTTPException(status_code=503, detail="Leonardo API key not configured")
    try:
        me = await LeonardoClient.get_me()
        u = (me.get("user_details") or [{}])[0]
        return {
            "username": (u.get("user") or {}).get("username"),
            "apiCreditBalance": u.get("apiCreditBalance"),
            "apiPlan": u.get("apiPlan"),
            "tokenBalance": u.get("tokenBalance"),
            "subscriptionTokens": (u.get("user") or {}).get("tokenBalance"),
        }
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Leonardo balance check failed: {e}")


@router.get("/leonardo-models")
async def leonardo_models():
    """List available Leonardo platform models (proxied, auth-gated)."""
    from app.creator.leonardo import LeonardoClient
    if not LeonardoClient.configured():
        raise HTTPException(status_code=503, detail="Leonardo API key not configured")
    try:
        return await LeonardoClient.list_models()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Leonardo model list failed: {e}")


@router.get("/personas", response_model=List[PersonaOut])
async def list_personas(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    _seed_personas(db)
    return db.query(models.Persona).all()


@router.post("/personas", response_model=PersonaOut)
async def create_persona(
    payload: PersonaCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    existing = db.query(models.Persona).filter(models.Persona.slug == payload.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail="Slug already exists")
    persona = models.Persona(**payload.dict())
    db.add(persona)
    db.commit()
    db.refresh(persona)
    return persona




class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    archetype: Optional[str] = None
    brief_json: Optional[dict] = None
    status: Optional[str] = None


@router.patch("/personas/{persona_id}", response_model=PersonaOut)
async def update_persona(
    persona_id: int,
    payload: PersonaUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    import json as _json
    data = payload.dict(exclude_unset=True)
    for k, v in data.items():
        if k == "brief_json" and isinstance(v, dict):
            v = _json.dumps(v)  # column is Text holding a JSON string
        setattr(persona, k, v)
    db.commit()
    db.refresh(persona)
    return persona


@router.post("/personas/{persona_id}/character-lock")
async def character_lock(
    persona_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Fire a generation batch of N=8 candidates from persona brief."""
    if not LeonardoClient.configured():
        raise HTTPException(status_code=503, detail="Leonardo API key not configured")

    persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Parse brief for prompt inspiration
    brief = {}
    try:
        brief = json.loads(persona.brief_json or "{}")
    except Exception:
        pass

    # Build prompts from brief DNA + look
    dna = brief.get("dna", "")
    look = brief.get("look", "")
    base_prompt = f"Portrait of a virtual influencer. {dna}. {look}. Studio lighting, neutral background, high detail, photorealistic."
    prompts = [f"{base_prompt} Angle variation {i+1}." for i in range(8)]

    # Create job record
    job = models.GenerationJob(
        persona_id=persona_id,
        purpose=models.JobPurpose.CHARACTER_LOCK,
        status=models.JobStatus.RUNNING,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    leonardo_ids = []
    total_credits = 0.0
    try:
        for prompt in prompts:
            result = await LeonardoClient.create_generation(
                prompt=prompt, num_images=1,
                model_id=os.getenv("LEONARDO_MODEL_ID") or None)
            gen_id = result.get("sdGenerationJob", {}).get("generationId")
            if gen_id:
                leonardo_ids.append(gen_id)
                # Stub credit tracking — real cost from poll
                total_credits += 1.0
                asset = models.CreatorAsset(
                    persona_id=persona_id,
                    kind=models.AssetKind.CANDIDATE,
                    leonardo_generation_id=gen_id,
                    prompt=prompt,
                    credits_used=1.0,
                    status="pending",
                )
                db.add(asset)
        job.leonardo_ids_json = json.dumps(leonardo_ids)
        job.credits_used = total_credits
        job.status = models.JobStatus.COMPLETED
    except Exception as exc:
        job.status = models.JobStatus.FAILED
        job.leonardo_ids_json = json.dumps({"error": str(exc)})
        db.commit()
        raise HTTPException(status_code=502, detail=f"Leonardo generation failed: {exc}")

    db.commit()
    db.refresh(job)
    return {"status": "ok", "job_id": job.id, "leonardo_ids": leonardo_ids}


@router.get("/personas/{persona_id}/candidates", response_model=List[AssetOut])
async def list_candidates(
    persona_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    return db.query(models.CreatorAsset).filter(
        models.CreatorAsset.persona_id == persona_id,
        models.CreatorAsset.kind == models.AssetKind.CANDIDATE
    ).all()


@router.post("/personas/{persona_id}/canonize")
async def canonize(
    persona_id: int,
    payload: CanonizeRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Mark selected candidates as canonical (training input)."""
    persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    assets = db.query(models.CreatorAsset).filter(
        models.CreatorAsset.id.in_(payload.asset_ids),
        models.CreatorAsset.persona_id == persona_id
    ).all()

    if len(assets) != len(payload.asset_ids):
        raise HTTPException(status_code=400, detail="Some asset IDs not found for this persona")

    for asset in assets:
        asset.kind = models.AssetKind.CANONICAL

    persona.status = models.PersonaStatus.CHARACTER_LOCK
    db.commit()
    return {"status": "ok", "canonized": len(assets)}


@router.post("/personas/{persona_id}/train", response_model=TrainResponse)
async def train_persona(
    persona_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Kick LoRA training from canonical set. STUBBED — returns plan, does not train yet."""
    if not LeonardoClient.configured():
        return {"status": "unconfigured", "message": "Leonardo API key not configured", "job_id": None}

    persona = db.query(models.Persona).filter(models.Persona.id == persona_id).first()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    canonical = db.query(models.CreatorAsset).filter(
        models.CreatorAsset.persona_id == persona_id,
        models.CreatorAsset.kind == models.AssetKind.CANONICAL
    ).all()

    if not canonical:
        raise HTTPException(status_code=400, detail="No canonical assets selected. Run character-lock and canonize first.")

    # STUB: Real training requires dataset upload + train_custom_model call
    # Phase A does not implement full training pipeline — only the scaffolding.
    job = models.GenerationJob(
        persona_id=persona_id,
        purpose=models.JobPurpose.LORA_TRAIN,
        status=models.JobStatus.PENDING,
        leonardo_ids_json=json.dumps({"note": "stubbed", "canonical_count": len(canonical)}),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "status": "stubbed",
        "message": f"LoRA training stubbed. {len(canonical)} canonical assets ready. Full training in Phase B.",
        "job_id": job.id,
    }


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    job = db.query(models.GenerationJob).filter(models.GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
