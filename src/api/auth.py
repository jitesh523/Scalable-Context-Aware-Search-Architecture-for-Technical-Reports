"""
Authentication and authorization middleware.
Handles JWT validation and API key security.
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta

from config.settings import settings

logger = logging.getLogger(__name__)
security = HTTPBearer()

class AuthHandler:
    """
    Handles JWT authentication.
    """
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.api.jwt_secret_key,
                algorithms=[settings.api.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
        """Dependency to get current user from token."""
        token = credentials.credentials
        payload = self.decode_token(token)
        return payload.get("sub")

def get_api_key(api_key_header: str = Depends(security)):
    """Validate API key for service-to-service calls."""
    # Placeholder for API key validation logic
    pass
