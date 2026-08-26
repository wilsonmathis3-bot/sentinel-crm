"""Posting adapter interface — Instagram, TikTok, Buffer stubs.
No live posting without credentials. Everything approval-gated.
"""
import os
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod

# Optional Buffer API token
BUFFER_TOKEN = os.getenv("BUFFER_TOKEN", "")


class PostingAdapter(ABC):
    """Abstract base for platform posting adapters."""
    
    @abstractmethod
    async def post(self, image_path: str, caption: str, hashtags: str = "") -> Dict[str, Any]:
        """Post content to platform. Returns {status, post_id, error}."""
        pass
    
    @abstractmethod
    def configured(self) -> bool:
        """Check if adapter has credentials."""
        pass


class InstagramAdapter(PostingAdapter):
    """Instagram Graph API adapter (stub until credentials configured)."""
    
    def __init__(self, access_token: str = None, account_id: str = None):
        self.access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        self.account_id = account_id or os.getenv("INSTAGRAM_ACCOUNT_ID", "")
    
    def configured(self) -> bool:
        return bool(self.access_token and self.account_id)
    
    async def post(self, image_path: str, caption: str, hashtags: str = "") -> Dict[str, Any]:
        if not self.configured():
            return {
                "status": "not_configured",
                "post_id": None,
                "error": "Instagram credentials not configured",
            }
        
        # STUB: Real implementation would:
        # 1. Upload image to Instagram Graph API
        # 2. Create media container
        # 3. Publish container
        return {
            "status": "stubbed",
            "post_id": None,
            "error": None,
            "note": "Instagram posting stubbed. Credentials exist but live posting disabled.",
        }


class TikTokAdapter(PostingAdapter):
    """TikTok Content Posting API adapter (stub)."""
    
    def __init__(self, access_token: str = None):
        self.access_token = access_token or os.getenv("TIKTOK_ACCESS_TOKEN", "")
    
    def configured(self) -> bool:
        return bool(self.access_token)
    
    async def post(self, image_path: str, caption: str, hashtags: str = "") -> Dict[str, Any]:
        if not self.configured():
            return {
                "status": "not_configured",
                "post_id": None,
                "error": "TikTok credentials not configured",
            }
        return {
            "status": "stubbed",
            "post_id": None,
            "error": None,
            "note": "TikTok posting stubbed. Credentials exist but live posting disabled.",
        }


class BufferAdapter(PostingAdapter):
    """Buffer API adapter (optional, only if BUFFER_TOKEN configured)."""
    
    def __init__(self, token: str = None):
        self.token = token or BUFFER_TOKEN
    
    def configured(self) -> bool:
        return bool(self.token)
    
    async def post(self, image_path: str, caption: str, hashtags: str = "") -> Dict[str, Any]:
        if not self.configured():
            return {
                "status": "not_configured",
                "post_id": None,
                "error": "Buffer token not configured",
            }
        return {
            "status": "stubbed",
            "post_id": None,
            "error": None,
            "note": "Buffer posting stubbed. Token exists but live posting disabled.",
        }


class AutoDMStub:
    """Auto-DM stub — no live sending. Approval-gated."""
    
    @staticmethod
    async def send_dm(recipient_id: str, message: str) -> Dict[str, Any]:
        return {
            "status": "stubbed",
            "sent": False,
            "note": "Auto-DM disabled. Human approval required.",
        }


class VoiceClipStub:
    """Voice clip stub — no live generation/sending."""
    
    @staticmethod
    async def generate_voice(text: str) -> Dict[str, Any]:
        return {
            "status": "stubbed",
            "audio_url": None,
            "note": "Voice clip generation disabled. Human approval required.",
        }


# Registry of adapters
ADAPTERS = {
    "instagram": InstagramAdapter(),
    "tiktok": TikTokAdapter(),
    "buffer": BufferAdapter(),
}


def get_adapter(platform: str) -> PostingAdapter:
    """Get adapter for platform."""
    return ADAPTERS.get(platform.lower(), InstagramAdapter())
