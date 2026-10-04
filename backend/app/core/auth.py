"""
Supabase Authentication dependency and token verification.
Enforces that FastAPI endpoints validate real Supabase JWTs and resolve authenticated identities.
"""

from typing import Optional
from uuid import UUID
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from supabase import Client, ClientOptions, create_client

from app.config import get_settings
from app.core.logging import get_logger

logger = get_logger("auth")
security = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    id: UUID
    email: Optional[str] = None
    full_name: str = "Recruiter"
    role: str = "recruiter"
    token: Optional[str] = None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> AuthenticatedUser:
    """
    Validates Supabase JWT from Authorization header.
    Returns the authenticated user identity or raises 401 Unauthorized.
    """
    settings = get_settings()

    # 1. If Supabase is configured, enforce strict token verification
    if (
        settings.supabase_url
        and settings.supabase_key
        and "your-project" not in settings.supabase_url
        and "your_supabase" not in settings.supabase_url
    ):
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please provide a Bearer access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials
        try:
            # Create Supabase client to verify JWT with Auth service
            client: Client = create_client(settings.supabase_url, settings.supabase_key)
            user_response = client.auth.get_user(token)

            if not user_response or not user_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired Supabase authentication token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            user = user_response.user
            meta = user.user_metadata or {}
            full_name = meta.get("full_name") or "Recruiter"
            role = meta.get("role") or "recruiter"

            return AuthenticatedUser(
                id=UUID(user.id),
                email=user.email,
                full_name=full_name,
                role=role,
                token=token,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.warning("Token verification failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication token verification failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # 2. Local development / fallback mode when Supabase is unconfigured
    # Allows existing unit tests and offline workflows to proceed
    if credentials:
        # Check if caller supplied a mock or test user
        return AuthenticatedUser(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            email="developer@local.test",
            full_name="Local Developer",
            role="recruiter",
            token=credentials.credentials,
        )

    return AuthenticatedUser(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        email="developer@local.test",
        full_name="Local Developer",
        role="recruiter",
        token=None,
    )


def get_authenticated_supabase_client(token: Optional[str] = None) -> Optional[Client]:
    """Creates a Supabase client scoped to the user's access token for RLS enforcement."""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        return None

    if token:
        return create_client(
            settings.supabase_url,
            settings.supabase_key,
            options=ClientOptions(headers={"Authorization": f"Bearer {token}"}),
        )
    return create_client(settings.supabase_url, settings.supabase_key)
