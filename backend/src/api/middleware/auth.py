"""Clerk JWT authentication middleware and dependency."""
import httpx
import json
import logging
from functools import lru_cache
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from jose.utils import base64url_decode
from pydantic import BaseModel

from src.core.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


class ClerkUser(BaseModel):
    user_id: str
    email: Optional[str] = None
    workspace_id: Optional[str] = None


_jwks_cache: Optional[dict] = None


async def _get_clerk_jwks() -> dict:
    """Fetch Clerk JWKS from the well-known endpoint. Cached in memory."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache
    
    jwks_url = f"{settings.clerk_jwt_issuer}/.well-known/jwks.json"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(jwks_url, timeout=10.0)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            logger.info("Fetched Clerk JWKS from %s", jwks_url)
            return _jwks_cache
    except Exception as e:
        logger.error("Failed to fetch Clerk JWKS: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )


def _find_key(jwks: dict, kid: str) -> Optional[dict]:
    """Find the key with the given kid in the JWKS."""
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    return None


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> ClerkUser:
    """FastAPI dependency — validates Clerk JWT and returns the authenticated user."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # In development/testing, allow a special bypass token
    if settings.app_env == "development" and token == "dev-bypass":
        logger.warning("Using development bypass token — NEVER use in production")
        return ClerkUser(user_id="dev-user-001", email="dev@example.com")
    
    try:
        # Decode the header to get the kid
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        
        if not kid:
            raise HTTPException(status_code=401, detail="Invalid token: no kid")
        
        # Get JWKS and find the matching key
        jwks = await _get_clerk_jwks()
        key = _find_key(jwks, kid)
        
        if not key:
            # Invalidate cache and retry once
            global _jwks_cache
            _jwks_cache = None
            jwks = await _get_clerk_jwks()
            key = _find_key(jwks, kid)
        
        if not key:
            raise HTTPException(status_code=401, detail="Invalid token: key not found")
        
        # Verify and decode the JWT
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: no sub claim")
        
        email = payload.get("email")
        
        # Extract workspace_id from custom Clerk session claims if available
        workspace_id = payload.get("workspace_id") or payload.get("public_metadata", {}).get("workspace_id")
        
        return ClerkUser(
            user_id=user_id,
            email=email,
            workspace_id=workspace_id,
        )
    
    except JWTError as e:
        logger.warning("JWT validation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
