"""Main module for Ralph's LRS API authentication."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import SecurityScopes

from ralph.api.auth.basic import AuthenticatedUser, get_basic_auth_user
from ralph.api.auth.cozy import get_cozy_user
from ralph.api.auth.oidc import get_oidc_user
from ralph.conf import settings


def get_authenticated_user(
    security_scopes: SecurityScopes,
    basic_auth_user: Annotated[AuthenticatedUser, Depends(get_basic_auth_user)],
    oidc_auth_user: Annotated[AuthenticatedUser, Depends(get_oidc_user)],
    cozy_auth_user: Annotated[AuthenticatedUser, Depends(get_cozy_user)],
) -> AuthenticatedUser:
    """Authenticate user with any allowed method, using credentials in the header."""
    if basic_auth_user:
        user = basic_auth_user
        auth_header = "Basic"
    elif oidc_auth_user:
        user = oidc_auth_user
        auth_header = "Bearer"
    elif cozy_auth_user:
        user = cozy_auth_user
        auth_header = "Bearer"
    else:
        auth_header = ",".join(
            [
                {"basic": "Basic", "oidc": "Bearer", "cozy": "Bearer"}[backend.value]
                for backend in settings.RUNSERVER_AUTH_BACKENDS
            ]
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": auth_header},
        )

    # Restrict access by scopes
    if settings.LRS_RESTRICT_BY_SCOPES:
        for requested_scope in security_scopes.scopes:
            if not user.scopes.is_authorized(requested_scope):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f'Access not authorized to scope: "{requested_scope}".',
                    headers={"WWW-Authenticate": auth_header},
                )
    return user
