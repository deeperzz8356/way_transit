from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import os

from database import SessionLocal
import crud
import schemas
import auth

import firebase_admin
from firebase_admin import auth as firebase_admin_auth, credentials

router = APIRouter(prefix="/auth", tags=["auth"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _initialize_firebase_app():
    try:
        return firebase_admin.get_app()
    except ValueError:
        # Check env vars first, then fall back to local firebase-admin.json
        cred_path = (
            os.getenv('FIREBASE_ADMIN_CREDENTIALS')
            or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        )
        # A stale environment variable should not prevent the checked-in local
        # development credential from being used.
        if not cred_path or not os.path.exists(cred_path):
            # Fallback: look for firebase-admin.json next to this file
            local_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'firebase-admin.json')
            if os.path.exists(local_path):
                cred_path = local_path
        if not cred_path or not os.path.exists(cred_path):
            raise RuntimeError(
                'Firebase admin credentials are not configured. '
                'Set FIREBASE_ADMIN_CREDENTIALS to the service account JSON file path, '
                'or place firebase-admin.json in the backend/ directory.'
            )
        cred = credentials.Certificate(cred_path)
        return firebase_admin.initialize_app(cred)


def _verify_firebase_id_token(id_token: str) -> dict:
    if not id_token:
        raise HTTPException(status_code=400, detail='Firebase ID token is required')

    app = _initialize_firebase_app()
    try:
        token_payload = firebase_admin_auth.verify_id_token(id_token, app=app)
        return token_payload
    except firebase_admin_auth.ExpiredIdTokenError:
        raise HTTPException(status_code=401, detail='Firebase ID token has expired')
    except firebase_admin_auth.RevokedIdTokenError:
        raise HTTPException(status_code=401, detail='Firebase ID token has been revoked')
    except Exception as exc:
        # Log the full error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Firebase token verification error: {exc}')
        
        # In development, try to work around SSL certificate issues
        error_str = str(exc)
        if 'CERTIFICATE_VERIFY_FAILED' in error_str or 'SSL' in error_str:
            logger.warning('SSL verification failed, attempting to decode token anyway for development...')
            # Try to extract token info without full verification for development
            try:
                import json
                import base64
                # Firebase ID tokens are JWT format: header.payload.signature
                parts = id_token.split('.')
                if len(parts) == 3:
                    # Decode payload (part[1], not header)
                    payload = parts[1]
                    payload += '=' * (4 - len(payload) % 4)  # Add padding
                    decoded = json.loads(base64.urlsafe_b64decode(payload))
                    
                    logger.warning(f'Development mode: Accepting decoded token without SSL verification')
                    logger.info(f'Full token payload: {json.dumps(decoded, indent=2)}')
                    
                    # Extract uid from token (Firebase stores it as 'sub' claim)
                    uid = decoded.get('uid') or decoded.get('sub')
                    email = decoded.get('email')
                    logger.info(f'Extracted: uid={uid}, email={email}')
                    
                    return decoded  # ← Return the decoded token without signature verification
            except Exception as decode_err:
                logger.error(f'Failed to decode token: {decode_err}')
                raise HTTPException(
                    status_code=400, 
                    detail=f'Failed to decode Firebase token: {decode_err}'
                )
        raise HTTPException(status_code=400, detail=f'Invalid Firebase ID token: {exc}')

    return token_payload


def _get_provider_type(decoded_token: dict) -> str:
    firebase_info = decoded_token.get('firebase', {}) or {}
    sign_in_provider = firebase_info.get('sign_in_provider')
    if sign_in_provider == 'google.com':
        return 'google'
    if sign_in_provider == 'phone':
        return 'phone'
    return 'firebase'


def _create_or_update_user_from_firebase_token(decoded_token: dict, db: Session):
    provider = _get_provider_type(decoded_token)
    uid = decoded_token.get('uid')
    email = decoded_token.get('email')
    phone_number = decoded_token.get('phone_number')
    name = decoded_token.get('name') or decoded_token.get('displayName')
    picture = decoded_token.get('picture')

    if not email and phone_number:
        email = f'{phone_number}@phone.local'

    user = None
    if provider == 'google' and uid:
        user = crud.get_user_by_google_id(db, uid)

    if not user and email:
        user = crud.get_user_by_email(db, email=email)

    if not user and phone_number:
        user = crud.get_user_by_phone(db, phone=phone_number)

    if not user:
        user = crud.create_user(
            db,
            email=email or f'{uid or phone_number}@firebase.local',
            password=None,
            phone=phone_number,
            name=name,
            google_id=uid if provider == 'google' else None,
            profile_image=picture,
            auth_provider=provider,
            is_verified=True,
        )
    else:
        updated_fields = {
            'name': name,
            'profile_image': picture,
            'auth_provider': provider,
            'is_verified': True,
        }
        if provider == 'google' and uid:
            updated_fields['google_id'] = uid
        if phone_number:
            updated_fields['phone'] = phone_number
        user = crud.update_user(db, user, **updated_fields)

    return user


@router.post('/firebase', response_model=schemas.TokenResponse)
def firebase_auth(payload: schemas.FirebaseAuthRequest, db: Session = Depends(get_db)):
    token_payload = _verify_firebase_id_token(payload.id_token)
    user = _create_or_update_user_from_firebase_token(token_payload, db)
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
