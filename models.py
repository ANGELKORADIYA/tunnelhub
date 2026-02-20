"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class TunnelStatus(str, Enum):
    """Tunnel status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    PENDING = "pending"


class UserConfig(BaseModel):
    """User configuration model."""
    id: str = Field(..., description="Unique user identifier (e.g., user_1)")
    name: str = Field(..., description="Display name for the user")
    ngrok_tokens: List[str] = Field(..., description="List of ngrok API tokens")
    ngrok_api_urls: List[str] = Field(default=["https://api.ngrok.com"], description="Ngrok API URLs")


class NgrokTunnel(BaseModel):
    """Ngrok tunnel model."""
    id: str = Field(..., description="Tunnel ID from ngrok")
    public_url: str = Field(..., description="Public URL of the tunnel")
    proto: str = Field(..., description="Protocol (http/https/tcp/tls)")
    region: str = Field(..., description="Tunnel region")
    tunnel_session_id: str = Field(..., description="Session ID")
    forwards_to: Optional[str] = Field(None, description="Local forward address")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class Tunnel(NgrokTunnel):
    """Extended tunnel model with custom naming and user assignment."""
    user_id: str = Field(..., description="User ID who owns this tunnel")
    user_name: str = Field(..., description="User display name")
    custom_name: Optional[str] = Field(None, description="Custom name for the tunnel")
    status: TunnelStatus = Field(default=TunnelStatus.ONLINE, description="Tunnel status")


class TunnelListResponse(BaseModel):
    """Response model for tunnel list endpoint."""
    success: bool = Field(..., description="Request success status")
    tunnels: List[Tunnel] = Field(default_factory=list, description="List of tunnels")
    total_count: int = Field(..., description="Total number of tunnels")
    filtered_user: Optional[str] = Field(None, description="User filter applied (if any)")
    timestamp: str = Field(..., description="Response timestamp")


class LoginRequest(BaseModel):
    """Login request model with encrypted password."""
    encrypted_password: str = Field(..., description="Base64-encoded RSA-encrypted password")


class LoginResponse(BaseModel):
    """Login response model."""
    success: bool = Field(..., description="Login success status")
    session_token: Optional[str] = Field(None, description="Session token for authenticated requests")
    message: str = Field(..., description="Response message")


class CustomNameRequest(BaseModel):
    """Request model for setting custom tunnel name."""
    custom_name: str = Field(..., min_length=1, max_length=100, description="Custom name for the tunnel")


class CustomNameResponse(BaseModel):
    """Response model for custom name update."""
    success: bool = Field(..., description="Update success status")
    message: str = Field(..., description="Response message")
    tunnel_id: str = Field(..., description="Tunnel ID")
    custom_name: str = Field(..., description="Updated custom name")


class UsersListResponse(BaseModel):
    """Response model for users list endpoint."""
    success: bool = Field(..., description="Request success status")
    users: List[UserConfig] = Field(default_factory=list, description="List of users")
    total_count: int = Field(..., description="Total number of users")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Server status")
    pid: int = Field(..., description="Process ID")
    platform: str = Field(..., description="Operating system platform")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")


class PublicKeyResponse(BaseModel):
    """Public key response model."""
    public_key: str = Field(..., description="RSA public key in PEM format")
    key_size: int = Field(..., description="RSA key size in bits")


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str = Field(..., description="Error details")
    status_code: int = Field(..., description="HTTP status code")


class SessionData(BaseModel):
    """Session data model."""
    session_token: str = Field(..., description="Session token")
    user_id: Optional[str] = Field(None, description="Associated user ID (if logged in as user)")
    is_admin: bool = Field(default=False, description="Admin session flag")
    created_at: str = Field(..., description="Session creation timestamp")
