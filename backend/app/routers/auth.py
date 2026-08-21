import time
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app import crud, schemas
from app.auth import create_access_token, verify_password, get_password_hash
from app.passkey import (
    generate_passkey_registration_options,
    verify_passkey_registration,
    generate_passkey_authentication_options,
    verify_passkey_authentication,
)

router = APIRouter()

# Login rate limiting: max 5 failed attempts per 60s per email (in-memory; move to Redis at scale)
_login_fails = defaultdict(list)
_MAX_FAILS = 5
_WINDOW = 60

def _check_rate_limit(key: str):
    now = time.time()
    _login_fails[key] = [t for t in _login_fails[key] if now - t < _WINDOW]
    if len(_login_fails[key]) >= _MAX_FAILS:
        raise HTTPException(status_code=429, detail="Too many failed attempts. Try again in a minute.")

def _record_fail(key: str):
    _login_fails[key].append(time.time())

@router.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(user.password) < 12:
        raise HTTPException(status_code=400, detail="Password must be at least 12 characters")
    
    hashed_password = get_password_hash(user.password)
    db_user = crud.create_user(db, email=user.email, hashed_password=hashed_password, full_name=user.full_name or "")
    return db_user

@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    _check_rate_limit(credentials.email.lower())
    db_user = crud.get_user_by_email(db, email=credentials.email)
    if not db_user or not verify_password(credentials.password, db_user.hashed_password):
        _record_fail(credentials.email.lower())
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    crud.update_user_last_login(db, db_user.id)
    access_token = create_access_token(data={"sub": db_user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }

@router.post("/passkey/register/start")
def passkey_register_start(data: schemas.PasskeyRegistrationStart):
    options = generate_passkey_registration_options(
        user_id=data.user_id,
        user_email=data.email,
        user_name=data.name
    )
    return options

@router.post("/passkey/register/verify")
def passkey_register_verify(data: schemas.PasskeyRegistrationVerify, db: Session = Depends(get_db)):
    result = verify_passkey_registration(data.user_id, data.response)
    
    user_id = int(data.user_id)
    crud.create_credential(
        db,
        user_id=user_id,
        credential_id=result["credential_id"],
        public_key=result["public_key"],
        device_name=data.device_name
    )
    crud.enable_passkey(db, user_id)
    
    return {"verified": True, "credential_id": result["credential_id"]}

@router.post("/passkey/auth/start")
def passkey_auth_start(data: schemas.PasskeyAuthStart, db: Session = Depends(get_db)):
    options = generate_passkey_authentication_options(data.credential_id)
    return options

@router.post("/passkey/auth/verify", response_model=schemas.Token)
def passkey_auth_verify(data: schemas.PasskeyAuthVerify, db: Session = Depends(get_db)):
    db_cred = crud.get_credential_by_credential_id(db, data.credential_id)
    if not db_cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    result = verify_passkey_authentication(
        credential_id=data.credential_id,
        response=data.response,
        public_key=bytes.fromhex(db_cred.public_key),
        current_sign_count=db_cred.sign_count
    )
    
    crud.update_credential_sign_count(db, data.credential_id, result["new_sign_count"])
    
    db_user = crud.get_user(db, db_cred.user_id)
    crud.update_user_last_login(db, db_user.id)
    access_token = create_access_token(data={"sub": db_user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": db_user
    }
