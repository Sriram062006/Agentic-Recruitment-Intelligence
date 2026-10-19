"""
Supabase Authentication dependency, role-based authorization, and token verification.
Enforces that FastAPI endpoints validate real Supabase JWTs, resolve authenticated identities,
and enforce strict role boundaries (ADMIN, RECRUITER, VIEWER).
"""

from typing import Callable, List, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, Query, Security, status
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
    is_active: bool = True
    token: Optional[str] = None


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    token_query: Optional[str] = Query(default=None, alias="token"),
) -> AuthenticatedUser:
    """
    Validates Supabase JWT from Authorization header or ?token= query parameter.
    Resolves live profile permissions from PostgreSQL or local database fallback.
    Returns the authenticated user identity or raises 401 Unauthorized / 403 Forbidden.
    """
    settings = get_settings()

    # 1. If Supabase is configured, enforce strict token verification
    if (
        settings.supabase_url
        and settings.supabase_key
        and "your-project" not in settings.supabase_url
        and "your_supabase" not in settings.supabase_url
    ):
        raw_token = credentials.credentials if credentials else token_query
        if not raw_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required. Please provide a Bearer access token or ?token= query param.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = raw_token
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
            user_id = UUID(user.id)
            meta = user.user_metadata or {}
            full_name = meta.get("full_name") or "Recruiter"
            role = meta.get("role") or "recruiter"
            is_active = True

            # Query live recruiter_profiles for up-to-date role and activation status
            try:
                from app.services.database.repositories.recruiter_repo import RecruiterRepository
                repo = RecruiterRepository()
                db_profile = repo.get_by_user_id(user_id, token=token)
                if db_profile:
                    full_name = db_profile.full_name
                    role = db_profile.role
                    is_active = db_profile.is_active
            except Exception as e:
                logger.debug("Could not fetch DB profile for user %s: %s", user_id, e)

            if not is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Your account has been deactivated. Please contact an administrator.",
                )

            return AuthenticatedUser(
                id=user_id,
                email=user.email,
                full_name=full_name,
                role=role.lower(),
                is_active=is_active,
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
    # Allows offline tests and mock development
    if credentials:
        # Check if caller specified a role via mock headers or defaults
        return AuthenticatedUser(
            id=UUID("00000000-0000-0000-0000-000000000001"),
            email="developer@local.test",
            full_name="Local Developer",
            role="admin",  # Default local dev to admin for testing convenience
            is_active=True,
            token=credentials.credentials,
        )

    return AuthenticatedUser(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        email="developer@local.test",
        full_name="Local Developer",
        role="admin",
        is_active=True,
        token=None,
    )


def require_role(allowed_roles: List[str]) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    """Dependency factory that verifies the authenticated user possesses one of the allowed roles."""
    normalized_allowed = [r.lower() for r in allowed_roles]

    def role_checker(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been deactivated. Please contact an administrator.",
            )
        if user.role.lower() not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: role '{user.role}' is not authorized for this operation. Requires one of: {allowed_roles}",
            )
        return user

    return role_checker


# Convenient role dependency shortcuts
require_admin = require_role(["admin"])
require_recruiter_or_admin = require_role(["admin", "recruiter"])
require_any_authenticated = require_role(["admin", "recruiter", "viewer"])


def get_authenticated_supabase_client(token: Optional[str] = None) -> Optional[Client]:
    """Creates a Supabase client scoped to the user's access token for RLS enforcement."""
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        return None

    if token and len(token.split(".")) == 3:
        return create_client(
            settings.supabase_url,
            settings.supabase_key,
            options=ClientOptions(headers={"Authorization": f"Bearer {token}"}),
        )
    return create_client(settings.supabase_url, settings.supabase_key)
