import os
import jwt
import requests
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jwt import PyJWKClient
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Azure AD configuration
AZURE_TENANT_ID = os.getenv('AZURE_TENANT_ID', os.getenv('REACT_APP_AZURE_TENANT_ID'))
AZURE_CLIENT_ID = os.getenv('AZURE_CLIENT_ID', os.getenv('REACT_APP_AZURE_CLIENT_ID'))

# Microsoft identity platform endpoints
AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
AZURE_JWKS_URI = f"{AZURE_AUTHORITY}/discovery/v2.0/keys"
AZURE_ISSUER = f"https://sts.windows.net/{AZURE_TENANT_ID}/"

# Initialize the security scheme
security = HTTPBearer(auto_error=False)

# Cache for JWKS client
jwks_client = None

def get_jwks_client():
    """Get or create JWKS client for token validation."""
    global jwks_client
    if jwks_client is None:
        jwks_client = PyJWKClient(AZURE_JWKS_URI)
    return jwks_client

def validate_token(token: str) -> dict:
    """Validate Azure AD token and return decoded claims."""
    try:
        # Get the signing key from Azure AD
        client = get_jwks_client()
        signing_key = client.get_signing_key_from_jwt(token)

        # Decode and validate the token
        decoded_token = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=AZURE_CLIENT_ID,
            issuer=AZURE_ISSUER,
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iss": True,
                "verify_exp": True,
                "verify_nbf": True,
                "require_exp": True,
                "require_nbf": False,
                "require_iat": True
            }
        )

        return decoded_token

    except jwt.ExpiredSignatureError:
        logger.error("Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidAudienceError:
        logger.error("Invalid audience")
        raise HTTPException(status_code=401, detail="Invalid audience")
    except jwt.InvalidIssuerError:
        logger.error("Invalid issuer")
        raise HTTPException(status_code=401, detail="Invalid issuer")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> dict:
    """Get current user from Azure AD token."""
    if not credentials:
        # For development, allow unauthenticated access if Azure AD is not configured
        if not AZURE_TENANT_ID or not AZURE_CLIENT_ID:
            logger.warning("Azure AD not configured, allowing unauthenticated access")
            return {"name": "Development User", "email": "dev@localhost"}
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = credentials.credentials
    user_info = validate_token(token)

    # Extract user information from token claims
    return {
        "id": user_info.get("oid", user_info.get("sub")),
        "name": user_info.get("name", user_info.get("preferred_username")),
        "email": user_info.get("email", user_info.get("upn")),
        "username": user_info.get("preferred_username"),
        "roles": user_info.get("roles", []),
        "groups": user_info.get("groups", [])
    }

async def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[dict]:
    """Optional authentication - returns user if authenticated, None otherwise."""
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None