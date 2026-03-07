"""Google OAuth + JWT authentication for Vercel deployment."""

import os
import time
import jwt
import requests as http_requests

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
APP_URL = os.environ.get("APP_URL", "http://127.0.0.1:5000")

JWT_EXPIRY = 60 * 60 * 24 * 30  # 30 days

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


def get_google_auth_url():
    """Build Google OAuth redirect URL."""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": f"{APP_URL}/auth/callback",
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
    }
    qs = "&".join(f"{k}={http_requests.utils.quote(v)}" for k, v in params.items())
    return f"{GOOGLE_AUTH_URL}?{qs}"


def exchange_code(code):
    """Exchange authorization code for tokens. Returns user info dict or None."""
    resp = http_requests.post(GOOGLE_TOKEN_URL, data={
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": f"{APP_URL}/auth/callback",
        "grant_type": "authorization_code",
    }, timeout=10)

    if resp.status_code != 200:
        return None

    tokens = resp.json()
    access_token = tokens.get("access_token")
    if not access_token:
        return None

    # Get user info
    info_resp = http_requests.get(GOOGLE_USERINFO_URL, headers={
        "Authorization": f"Bearer {access_token}",
    }, timeout=10)

    if info_resp.status_code != 200:
        return None

    return info_resp.json()


def create_jwt(user_id, email, name):
    """Create a signed JWT token."""
    payload = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRY,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_jwt(token):
    """Verify and decode JWT. Returns payload dict or None."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_current_user(request):
    """Extract current user from request cookies. Returns payload or None."""
    token = request.cookies.get("auth_token")
    if not token:
        return None
    return verify_jwt(token)
