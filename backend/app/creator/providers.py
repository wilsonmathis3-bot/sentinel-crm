"""Image generation provider layer.

Provider interface + three implementations:
- PerchanceProvider  (free, reverse-engineered)
- PollinationsProvider (free, URL-based)
- LeonardoClient     (paid, kept as-is in leonardo.py)

Migration lesson (import before constants):
  All os.getenv calls live BELOW imports so module-level env reads
  don't fail when this file is imported during alembic or model loading.
"""

import os
import re
import json
import uuid
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from urllib.parse import quote

import httpx

# ---------------------------------------------------------------------------
# Constants — declared AFTER imports to avoid circular/env issues
# ---------------------------------------------------------------------------
DEFAULT_IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "perchance")
PERCHANCE_API_BASE = "https://image-generation.perchance.org/api"
POLLINATIONS_API_BASE = "https://image.pollinations.ai"


# ---------------------------------------------------------------------------
# Provider interface
# ---------------------------------------------------------------------------
class ImageProvider(ABC):
    """Abstract image provider."""

    name: str = "abstract"

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        negative_prompt: str = "",
        guidance_scale: float = 7.0,
        seed: int = -1,
    ) -> Dict[str, Any]:
        """Generate an image.

        Returns dict with keys:
            image_url: str   (public URL or local path)
            provider: str    (provider name)
            cost: float      (USD or credit cost, 0.0 for free tiers)
        """
        ...


# ---------------------------------------------------------------------------
# PerchanceProvider — reverse-engineered free tier
# ---------------------------------------------------------------------------
class PerchanceProvider(ImageProvider):
    """Free image generation via perchance.org internal API.

    No official API — endpoint discovered from browser network tab.
    Generous timeouts + clean failure per principal order.
    """

    name = "perchance"

    def __init__(self, timeout: float = 120.0):
        self.timeout = timeout
        # userKey is a 64-char hex string observed in network traffic
        self._user_key = self._mk_user_key()

    @staticmethod
    def _mk_user_key() -> str:
        """Generate a fresh userKey (64-char hex)."""
        return uuid.uuid4().hex * 2  # 64 chars

    async def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        negative_prompt: str = "",
        guidance_scale: float = 7.0,
        seed: int = -1,
    ) -> Dict[str, Any]:
        resolution = f"{width}x{height}"
        request_id = random.random()
        cache_bust = random.random()

        # Perchance expects prompt wrapped in single quotes
        prompt_quoted = quote(f"'{prompt}'")
        neg_quoted = quote(f"'{negative_prompt}'") if negative_prompt else quote("''")

        create_params = {
            "prompt": prompt_quoted,
            "negativePrompt": neg_quoted,
            "userKey": self._user_key,
            "__cache_bust": cache_bust,
            "seed": str(seed),
            "resolution": resolution,
            "guidanceScale": str(guidance_scale),
            "channel": "ai-text-to-image-generator",
            "subChannel": "public",
            "requestId": request_id,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # 1) Create generation
            create_resp = await client.get(
                f"{PERCHANCE_API_BASE}/generate", params=create_params
            )
            create_resp.raise_for_status()
            create_data = create_resp.json()

            if "invalid_key" in create_data.get("error", "").lower():
                raise RuntimeError("Perchance returned invalid_key")

            image_id = create_data.get("imageId")
            if not image_id:
                raise RuntimeError(f"Perchance no imageId: {create_data}")

            # 2) Download image bytes
            dl_resp = await client.get(
                f"{PERCHANCE_API_BASE}/downloadTemporaryImage",
                params={"imageId": image_id},
            )
            dl_resp.raise_for_status()

            # 3) Persist locally under assets path
            assets_dir = os.getenv("CREATOR_ASSETS_PATH", "/app/backend/creator_assets")
            os.makedirs(assets_dir, exist_ok=True)
            local_name = f"perchance_{uuid.uuid4().hex[:12]}.jpeg"
            local_path = os.path.join(assets_dir, local_name)
            with open(local_path, "wb") as f:
                f.write(dl_resp.content)

        return {
            "image_url": local_path,  # local path since images are temporary
            "provider": self.name,
            "cost": 0.0,
        }


# ---------------------------------------------------------------------------
# PollinationsProvider — dead-simple free URL API
# ---------------------------------------------------------------------------
class PollinationsProvider(ImageProvider):
    """Free image generation via pollinations.ai.

    Endpoint: GET https://image.pollinations.ai/prompt/{prompt}?width=W&height=H
    Returns raw JPEG/PNG directly — no key, no queue.
    """

    name = "pollinations"

    def __init__(self, timeout: float = 60.0):
        self.timeout = timeout

    async def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        negative_prompt: str = "",
        guidance_scale: float = 7.0,
        seed: int = -1,
    ) -> Dict[str, Any]:
        # Pollinations uses URL-encoded prompt in path; nologo strips watermark
        safe_prompt = quote(prompt, safe="")
        url = (
            f"{POLLINATIONS_API_BASE}/prompt/{safe_prompt}"
            f"?width={width}&height={height}&nologo=true"
        )
        if seed != -1:
            url += f"&seed={seed}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(url)
            resp.raise_for_status()

            # Persist locally
            assets_dir = os.getenv("CREATOR_ASSETS_PATH", "/app/backend/creator_assets")
            os.makedirs(assets_dir, exist_ok=True)
            ext = "png" if "png" in resp.headers.get("content-type", "").lower() else "jpeg"
            local_name = f"pollinations_{uuid.uuid4().hex[:12]}.{ext}"
            local_path = os.path.join(assets_dir, local_name)
            with open(local_path, "wb") as f:
                f.write(resp.content)

        return {
            "image_url": local_path,
            "provider": self.name,
            "cost": 0.0,
        }


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------
PROVIDERS: Dict[str, Any] = {
    "perchance": PerchanceProvider,
    "pollinations": PollinationsProvider,
    # "leonardo" lives in leonardo.py and is wired manually where needed
}


def get_provider(name: Optional[str] = None) -> ImageProvider:
    """Return an instantiated provider by name.

    Defaults to IMAGE_PROVIDER env var (perchance if unset).
    """
    name = (name or DEFAULT_IMAGE_PROVIDER).lower()
    cls = PROVIDERS.get(name)
    if not cls:
        raise ValueError(f"Unknown image provider '{name}'. Available: {list(PROVIDERS.keys())}")
    return cls()


async def generate_with_fallback(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    primary: Optional[str] = None,
    fallback: Optional[str] = "pollinations",
) -> Dict[str, Any]:
    """Try primary provider, fall back to secondary on any error.

    Logs provider + zero cost on success.
    """
    primary_name = primary or DEFAULT_IMAGE_PROVIDER
    providers_to_try = [primary_name]
    if fallback and fallback != primary_name:
        providers_to_try.append(fallback)

    last_error = None
    for pname in providers_to_try:
        try:
            provider = get_provider(pname)
            result = await provider.generate(prompt, width=width, height=height)
            result["fallback_used"] = pname != primary_name
            return result
        except Exception as exc:
            last_error = exc
            continue

    raise RuntimeError(
        f"All providers failed ({providers_to_try}). Last error: {last_error}"
    )
