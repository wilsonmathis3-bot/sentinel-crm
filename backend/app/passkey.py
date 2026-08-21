import os
import json
import secrets
from typing import Dict, Optional
from fastapi import HTTPException
from webauthn import generate_registration_options, verify_registration_response
from webauthn import generate_authentication_options, verify_authentication_response
from webauthn.helpers.options_to_json import options_to_json
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    ResidentKeyRequirement,
)

RP_ID = os.getenv("PASSKEY_RP_ID", "localhost")
RP_NAME = "Sentinel CRM"
ORIGIN = os.getenv("PASSKEY_ORIGIN", "http://localhost:3000")

# In-memory challenge store (use Redis in production)
challenge_store: Dict[str, bytes] = {}

def generate_passkey_registration_options(user_id: str, user_email: str, user_name: str) -> dict:
    """Generate WebAuthn registration options for a new passkey"""
    challenge = secrets.token_bytes(32)
    challenge_store[f"reg_{user_id}"] = challenge
    
    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=user_id.encode(),
        user_name=user_email,
        user_display_name=user_name,
        challenge=challenge,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        exclude_credentials=[],
    )
    
    return json.loads(options_to_json(options))

def verify_passkey_registration(user_id: str, response: dict) -> dict:
    """Verify a passkey registration response"""
    challenge = challenge_store.pop(f"reg_{user_id}", None)
    if not challenge:
        raise HTTPException(status_code=400, detail="Registration challenge expired")
    
    try:
        verification = verify_registration_response(
            credential=response,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
        )
        return {
            "verified": True,
            "credential_id": verification.credential_id.hex(),
            "public_key": verification.credential_public_key.hex(),
            "sign_count": verification.sign_count,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration verification failed: {str(e)}")

def generate_passkey_authentication_options(credential_id: Optional[str] = None) -> dict:
    """Generate WebAuthn authentication options"""
    challenge = secrets.token_bytes(32)
    challenge_store[f"auth_{challenge.hex()}"] = challenge
    
    allow_credentials = []
    if credential_id:
        from webauthn.helpers.structs import PublicKeyCredentialDescriptor
        allow_credentials = [PublicKeyCredentialDescriptor(id=bytes.fromhex(credential_id))]
    
    options = generate_authentication_options(
        rp_id=RP_ID,
        challenge=challenge,
        allow_credentials=allow_credentials,
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    
    result = json.loads(options_to_json(options))
    result["challenge_hex"] = challenge.hex()
    return result

def verify_passkey_authentication(credential_id: str, response: dict, public_key: bytes, current_sign_count: int) -> dict:
    """Verify a passkey authentication response"""
    challenge_hex = response.get("challenge_hex", "")
    challenge = challenge_store.pop(f"auth_{challenge_hex}", None)
    if not challenge:
        raise HTTPException(status_code=400, detail="Authentication challenge expired")
    
    try:
        verification = verify_authentication_response(
            credential=response,
            expected_challenge=challenge,
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            credential_public_key=public_key,
            credential_current_sign_count=current_sign_count,
        )
        return {
            "verified": True,
            "new_sign_count": verification.new_sign_count,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication verification failed: {str(e)}")
