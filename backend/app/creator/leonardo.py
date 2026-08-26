"""Leonardo AI client — pure HTTP, zero LLM calls.
Bearer auth from env LEONARDO_API_KEY only.
"""
import os
from typing import Dict, Any, Optional
import httpx

LEONARDO_API_KEY = os.getenv("LEONARDO_API_KEY", "")
LEONARDO_BASE_URL = "https://cloud.leonardo.ai/api/rest/v1"


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {LEONARDO_API_KEY}",
        "Content-Type": "application/json",
    }


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=LEONARDO_BASE_URL, headers=_headers(), timeout=60.0)


class LeonardoClient:
    """Thin wrapper around Leonardo AI REST API."""

    @staticmethod
    def configured() -> bool:
        return bool(LEONARDO_API_KEY)

    @staticmethod
    async def create_generation(prompt: str, model_id: Optional[str] = None,
                                 num_images: int = 1, width: int = 1024, height: int = 1024,
                                 negative_prompt: str = "", guidance_scale: int = 7) -> Dict[str, Any]:
        """Create a new image generation job."""
        payload = {
            "prompt": prompt,
            "num_images": num_images,
            "width": width,
            "height": height,
            "negative_prompt": negative_prompt,
            "guidance_scale": guidance_scale,
        }
        if model_id:
            payload["modelId"] = model_id

        async with _client() as client:
            resp = await client.post("/generations", json=payload)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def get_generation(generation_id: str) -> Dict[str, Any]:
        """Poll generation status and results."""
        async with _client() as client:
            resp = await client.get(f"/generations/{generation_id}")
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def upload_dataset_image(file_content: bytes, file_name: str) -> Dict[str, Any]:
        """Upload a single image for custom model training dataset."""
        async with _client() as client:
            # Initiate upload
            resp = await client.post("/dataset-images", json={"extension": file_name.split(".")[-1]})
            resp.raise_for_status()
            upload_data = resp.json()
            upload_url = upload_data.get("uploadUrl")
            dataset_image_id = upload_data.get("datasetImageId")

            if not upload_url:
                raise RuntimeError("No uploadUrl returned from Leonardo")

            # PUT to presigned URL
            put_resp = await httpx.AsyncClient().put(
                upload_url,
                content=file_content,
                headers={"Content-Type": "application/octet-stream"}
            )
            put_resp.raise_for_status()
            return {"dataset_image_id": dataset_image_id, "upload_url": upload_url}

    @staticmethod
    async def train_custom_model(name: str, dataset_id: str,
                                  resolution: int = 512,
                                  instance_prompt: str = "") -> Dict[str, Any]:
        """Start LoRA training from a dataset."""
        payload = {
            "name": name,
            "datasetId": dataset_id,
            "resolution": resolution,
        }
        if instance_prompt:
            payload["instancePrompt"] = instance_prompt

        async with _client() as client:
            resp = await client.post("/custom-models", json=payload)
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def get_custom_model(model_id: str) -> Dict[str, Any]:
        """Get custom model status."""
        async with _client() as client:
            resp = await client.get(f"/custom-models/{model_id}")
            resp.raise_for_status()
            return resp.json()

    @staticmethod
    async def create_dataset(name: str, description: str = "") -> Dict[str, Any]:
        """Create a dataset for training images."""
        payload = {"name": name}
        if description:
            payload["description"] = description
        async with _client() as client:
            resp = await client.post("/datasets", json=payload)
            resp.raise_for_status()
            return resp.json()
