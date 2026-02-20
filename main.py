"""
TunnelHub - Main FastAPI Application
A secure ngrok tunnel management dashboard with RSA encryption, user-wise filtering, and auto-refresh.
"""

import os
import sys
import json
import time
import asyncio
import secrets
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, status, Request, Response, Body, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

# Import our modules
import security
import models

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="TunnelHub",
    description="Secure ngrok tunnel management dashboard",
    version="1.0.0"
)

# Configuration
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
RSA_KEY_SIZE = int(os.getenv("RSA_KEY_SIZE", "2048"))
AUTO_REFRESH_INTERVAL = int(os.getenv("AUTO_REFRESH_INTERVAL", "5"))
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "120"))
MAX_REQUEST_SIZE = int(os.getenv("MAX_REQUEST_SIZE", str(5 * 1024 * 1024)))

# Parse users from environment
try:
    USERS_JSON = os.getenv("USERS", "[]")
    USERS_CONFIG: List[models.UserConfig] = [
        models.UserConfig(**user) for user in json.loads(USERS_JSON)
    ]
except Exception as e:
    print(f"⚠️ Warning: Failed to parse USERS from environment: {e}")
    USERS_CONFIG = []

# Create users lookup dict
USERS_MAP: Dict[str, models.UserConfig] = {user.id: user for user in USERS_CONFIG}

# In-memory session storage
sessions: Dict[str, models.SessionData] = {}

# In-memory custom names storage (tunnel_id -> custom_name)
custom_names: Dict[str, str] = {}

# Server start time
SERVER_START_TIME = time.time()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Ensure RSA keys exist on startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    print("\n" + "="*60)
    print("🚀 Starting TunnelHub")
    print("="*60)

    # Ensure RSA keys exist
    security.ensure_keys_exist(RSA_KEY_SIZE)

    # Print configuration
    print(f"📊 Configuration:")
    print(f"   - Users: {len(USERS_CONFIG)}")
    print(f"   - Auto-refresh: {AUTO_REFRESH_INTERVAL}s")
    print(f"   - Rate limit: {RATE_LIMIT_RPM} RPM")
    print(f"   - RSA key size: {RSA_KEY_SIZE}-bit")
    print(f"   - Max request size: {MAX_REQUEST_SIZE / 1024 / 1024:.1f}MB")
    print("="*60 + "\n")


# =============================================================================
# Middleware
# =============================================================================

@app.middleware("http")
async def dos_protection(request: Request, call_next):
    """DoS protection middleware with rate limiting."""
    # Skip rate limiting for public endpoints
    if request.url.path in ["/", "/api/public-key", "/favicon.ico", "/docs", "/openapi.json"]:
        response = await call_next(request)
        return response

    # Initialize rate limiter
    if not hasattr(dos_protection, "_store"):
        dos_protection._store = {}
        dos_protection._lock = asyncio.Lock()

    client = request.client.host if request.client else "unknown"
    now = time.time()
    refill_per_sec = RATE_LIMIT_RPM / 60.0

    async with dos_protection._lock:
        entry = dos_protection._store.get(client)
        if not entry:
            entry = {"tokens": float(RATE_LIMIT_RPM), "last": now}
            dos_protection._store[client] = entry

        # Refill tokens
        elapsed = now - entry["last"]
        if elapsed > 0:
            entry["tokens"] = min(float(RATE_LIMIT_RPM), entry["tokens"] + elapsed * refill_per_sec)
            entry["last"] = now

        if entry["tokens"] < 1.0:
            retry_after = int(max(1, (1.0 - entry["tokens"]) / refill_per_sec))
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(retry_after)}
            )

        entry["tokens"] -= 1.0

    # Check request size
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_SIZE:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Request body too large"}
                )
        except ValueError:
            pass

    response = await call_next(request)
    return response


async def verify_session(request: Request) -> Optional[models.SessionData]:
    """Verify session token from request headers."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    session_token = auth_header[7:]  # Remove "Bearer " prefix
    return sessions.get(session_token)


def require_session():
    """Decorator to require valid session."""
    async def dependency(request: Request):
        session = await verify_session(request)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing session token"
            )
        return session
    return dependency


# =============================================================================
# API Endpoints - Authentication
# =============================================================================

@app.get("/api/public-key", response_model=models.PublicKeyResponse)
async def get_public_key():
    """
    Get RSA public key for password encryption.

    Returns the RSA public key in PEM format that the frontend should use
    to encrypt passwords before sending them to the server.
    """
    try:
        public_key_pem = security.get_public_key_pem()
        return models.PublicKeyResponse(
            public_key=public_key_pem,
            key_size=RSA_KEY_SIZE
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@app.post("/api/verify", response_model=models.LoginResponse)
async def verify_login(request_data: models.LoginRequest):
    """
    Verify login credentials with RSA-encrypted password.

    Expects a base64-encoded password that was encrypted using the RSA public key.
    Returns a session token on successful authentication.
    """
    try:
        # Decrypt the password
        password = security.decrypt_password(request_data.encrypted_password)

        # Verify against admin password
        if security.verify_password(password, ADMIN_PASSWORD):
            # Create session
            session_token = security.generate_session_token()
            session_data = models.SessionData(
                session_token=session_token,
                is_admin=True,
                created_at=datetime.now().isoformat()
            )
            sessions[session_token] = session_data

            return models.LoginResponse(
                success=True,
                session_token=session_token,
                message="Login successful"
            )

        return models.LoginResponse(
            success=False,
            message="Invalid password"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@app.post("/api/logout")
async def logout(request: Request):
    """
    Logout current session.

    Invalidates the current session token.
    """
    session = await verify_session(request)
    if session:
        del sessions[session.session_token]

    return {"success": True, "message": "Logged out successfully"}


# =============================================================================
# API Endpoints - Tunnel Management
# =============================================================================

async def fetch_ngrok_tunnels(token: str, api_url: str = "https://api.ngrok.com") -> List[Dict[str, Any]]:
    """
    Fetch tunnels from ngrok API for a specific token.

    Args:
        token: Ngrok API token
        api_url: Ngrok API URL

    Returns:
        List of tunnel data from ngrok API
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Ngrok-Version": "2",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(f"{api_url}/tunnels", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("tunnels", [])
        else:
            print(f"⚠️ Ngrok API error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"⚠️ Failed to fetch tunnels: {e}")
        return []


@app.get("/api/tunnels", response_model=models.TunnelListResponse)
async def get_tunnels(
    request: Request,
    user_id: Optional[str] = None
):
    """
    Get all tunnels with optional user filtering.

    Args:
        request: FastAPI request object
        user_id: Optional user ID to filter tunnels

    Returns:
        List of tunnels with metadata
    """
    # Verify session (optional - allow read access without auth for now)
    session = await verify_session(request)

    all_tunnels = []

    # Fetch tunnels for each user (or specific user if filtered)
    users_to_fetch = [USERS_MAP[user_id]] if user_id and user_id in USERS_MAP else USERS_CONFIG

    for user in users_to_fetch:
        for token_idx, token in enumerate(user.ngrok_tokens):
            api_url = user.ngrok_api_urls[min(token_idx, len(user.ngrok_api_urls) - 1)]

            # Fetch tunnels from ngrok API
            ngrok_tunnels = await fetch_ngrok_tunnels(token, api_url)

            # Process each tunnel
            for tunnel_data in ngrok_tunnels:
                tunnel_id = tunnel_data.get("id", "")

                # Create tunnel model
                tunnel = models.Tunnel(
                    id=tunnel_id,
                    public_url=tunnel_data.get("public_url", ""),
                    proto=tunnel_data.get("proto", ""),
                    region=tunnel_data.get("region", ""),
                    tunnel_session_id=tunnel_data.get("tunnel_session_id", ""),
                    forwards_to=tunnel_data.get("forwards_to"),
                    created_at=tunnel_data.get("created_at"),
                    metadata=tunnel_data.get("metadata", {}),
                    user_id=user.id,
                    user_name=user.name,
                    custom_name=custom_names.get(tunnel_id),
                    status=models.TunnelStatus.ONLINE
                )

                all_tunnels.append(tunnel)

    return models.TunnelListResponse(
        success=True,
        tunnels=all_tunnels,
        total_count=len(all_tunnels),
        filtered_user=user_id,
        timestamp=datetime.now().isoformat()
    )


@app.put("/api/tunnels/{tunnel_id}/name", response_model=models.CustomNameResponse)
async def set_tunnel_name(
    tunnel_id: str,
    request_data: models.CustomNameRequest,
    request: Request
):
    """
    Set a custom name for a tunnel.

    Args:
        tunnel_id: ID of the tunnel
        request_data: Request with custom name
        request: FastAPI request object

    Returns:
        Updated tunnel information
    """
    # Verify session
    session = await verify_session(request)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    # Store custom name
    custom_names[tunnel_id] = request_data.custom_name

    return models.CustomNameResponse(
        success=True,
        message="Custom name updated successfully",
        tunnel_id=tunnel_id,
        custom_name=request_data.custom_name
    )


# Future endpoints (not implemented yet)
@app.get("/api/tunnels/health/{tunnel_id}")
async def get_tunnel_health(tunnel_id: str):
    """Check tunnel health status (future implementation)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Tunnel health check not yet implemented"
    )


@app.delete("/api/tunnels/{tunnel_id}")
async def delete_tunnel(tunnel_id: str, request: Request):
    """Delete a tunnel (future implementation)."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Tunnel deletion not yet implemented"
    )


# =============================================================================
# API Endpoints - Admin
# =============================================================================

@app.get("/api/users", response_model=models.UsersListResponse)
async def get_users():
    """
    Get list of all users (admin endpoint).

    Returns configuration for all users.
    """
    return models.UsersListResponse(
        success=True,
        users=USERS_CONFIG,
        total_count=len(USERS_CONFIG)
    )


@app.get("/api/health", response_model=models.HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns server status and uptime.
    """
    uptime = time.time() - SERVER_START_TIME

    return models.HealthResponse(
        status="running",
        pid=os.getpid(),
        platform=sys.platform,
        uptime_seconds=round(uptime, 2)
    )


@app.post("/api/restart")
async def restart_server(
    background_tasks: BackgroundTasks,
    password: str = Body(..., embed=True)
):
    """
    Restart the server (admin only).

    Requires admin password authentication.
    """
    if not secrets.compare_digest(password, ADMIN_PASSWORD):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin password"
        )

    async def _restart_process(delay: int = 1):
        await asyncio.sleep(delay)
        python = sys.executable
        args = sys.argv
        print("Restarting server...")
        if sys.platform == 'win32':
            os.execv(python, ['python'] + args)
        else:
            os.execv(python, [python] + args)

    background_tasks.add_task(_restart_process)
    return {"success": True, "message": "Server restart initiated"}


# =============================================================================
# Frontend Routes
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Serve the main dashboard HTML.
    """
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "app_name": "TunnelHub",
            "auto_refresh_interval": AUTO_REFRESH_INTERVAL
        }
    )


# =============================================================================
# Root endpoint
# =============================================================================

@app.get("/api")
async def api_root():
    """
    API root endpoint with information.
    """
    return {
        "name": "TunnelHub API",
        "version": "1.0.0",
        "description": "Secure ngrok tunnel management dashboard",
        "endpoints": {
            "authentication": {
                "GET /api/public-key": "Get RSA public key for encryption",
                "POST /api/verify": "Verify login with encrypted password",
                "POST /api/logout": "Logout current session"
            },
            "tunnels": {
                "GET /api/tunnels": "Get all tunnels (with optional user filter)",
                "PUT /api/tunnels/{id}/name": "Set custom tunnel name"
            },
            "admin": {
                "GET /api/users": "Get list of users",
                "GET /api/health": "Server health check",
                "POST /api/restart": "Restart server"
            }
        },
        "documentation": "/docs"
    }


# =============================================================================
# Main entry point
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*60)
    print("🚀 TunnelHub Server")
    print("="*60)
    print(f"📖 Documentation: http://localhost:8000/docs")
    print(f"🌐 Dashboard: http://localhost:8000/")
    print(f"⚙️  Auto-refresh: {AUTO_REFRESH_INTERVAL}s")
    print("="*60 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True
    )
