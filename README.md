<p align="center">
  <img src="static/logo.png" alt="TunnelHub Logo" width="300">
</p>

# TunnelHub

A secure ngrok tunnel management dashboard with RSA encryption, user-wise filtering, custom tunnel naming, and auto-refresh capabilities. Built with FastAPI and featuring enterprise-grade security for managing multiple ngrok tunnels across different users.

## ✨ Features

- 🔐 **RSA Encryption**: Passwords are encrypted with RSA before transmission (2048-bit keys)
- 👥 **Multi-User Support**: Manage tunnels for multiple users with individual ngrok tokens
- 🏷️ **Custom Naming**: Set custom names for tunnels for easy identification
- 🔄 **Auto-Refresh**: Configurable auto-refresh to keep tunnel status up-to-date (default: 5 seconds)
- 🎨 **Modern UI**: Beautiful glassmorphism design with smooth animations
- 📊 **User Filtering**: View tunnels for specific users or all users at once
- 📋 **One-Click Copy**: Easily copy tunnel URLs to clipboard
- 🚀 **FastAPI Backend**: High-performance async API with rate limiting
- 🌐 **Vercel Support**: Serverless deployment ready with in-memory key management
- ⚡ **Async Operations**: Non-blocking tunnel fetching from ngrok API

## 📋 Requirements

- Python 3.8 or higher
- pip (Python package manager)

## 🚀 Installation

### 1. Clone or Navigate to TunnelHub Directory

```bash
cd TunnelHub
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Admin Security
ADMIN_PASSWORD=admin123                    # Change this to a secure password
RSA_KEY_SIZE=2048                          # RSA key size (2048 or 4096)

# Users Configuration (JSON array format)
USERS=[
    {
        "id": "user_1",
        "name": "John Doe",
        "ngrok_tokens": ["your_ngrok_token_1"],
        "ngrok_api_urls": ["https://api.ngrok.com"]
    },
    {
        "id": "user_2",
        "name": "Jane Smith",
        "ngrok_tokens": ["your_ngrok_token_2"],
        "ngrok_api_urls": ["https://api.ngrok.com"]
    }
]

# Application Settings
AUTO_REFRESH_INTERVAL=5                    # Auto-refresh interval in seconds
RATE_LIMIT_RPM=120                         # Rate limit per minute
MAX_REQUEST_SIZE=5242880                   # Max request size (5MB)
```

### 4. Get Ngrok API Tokens

To use TunnelHub, you need ngrok API tokens:

1. Sign up at [ngrok.com](https://ngrok.com)
2. Go to your dashboard
3. Navigate to "Your Authtoken"
4. Copy your authtoken and add it to the `ngrok_tokens` array in `.env`

## 🎮 Usage

### Starting the Server

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Or simply run:

```bash
python main.py
```

### Accessing the Dashboard

Open your browser and navigate to:

```
http://localhost:8000
```

### First Login

1. Enter the admin password (default: `admin123`)
2. The password will be encrypted with RSA before sending
3. Upon successful login, you'll see the dashboard

### Using the Dashboard

- **View All Tunnels**: See all tunnels from all users
- **Filter by User**: Click on a user in the sidebar to filter
- **Custom Names**: Click "Rename" on a tunnel to set a custom name
- **Copy URLs**: Click "Copy URL" to copy tunnel URL to clipboard
- **Open Tunnels**: Click "Open" to open tunnel in new tab
- **Toggle Auto-Refresh**: Click the pause/play button in the header

## 📁 Project Structure

```
TunnelHub/
├── main.py                     # FastAPI application with API endpoints
├── security.py                 # RSA encryption utilities & key management
├── models.py                   # Pydantic models for validation
├── setup_vercel_keys.py        # Utility to generate keys for Vercel
├── static/
│   ├── css/
│   │   └── style.css          # Dashboard styling with glassmorphism
│   └── js/
│       └── app.js             # Frontend logic with RSA encryption
├── templates/
│   └── index.html             # Dashboard HTML template
├── scripts/install/
│   ├── start.bat              # Windows startup script
│   └── start.sh               # Linux/Mac startup script
├── keys/                      # RSA keys (auto-generated on first run)
│   ├── private_key.pem        # ⚠️ NEVER commit or share this
│   └── public_key.pem         # Safe to distribute
├── requirements.txt            # Python dependencies
├── .env.example               # Environment configuration template
├── .env                       # Your configuration (create this)
└── README.md                  # This file
```

### File Descriptions

| File | Purpose |
|------|---------|
| [main.py](main.py) | FastAPI app with middleware, endpoints, and tunnel fetching |
| [security.py](security.py) | RSA key generation, encryption/decryption, session tokens |
| [models.py](models.py) | Pydantic models for request/response validation |
| [static/js/app.js](static/js/app.js) | Frontend with JSEncrypt, authentication, auto-refresh |
| [static/css/style.css](static/css/style.css) | Modern glassmorphism UI styling |
| [templates/index.html](templates/index.html) | Dashboard HTML template |

## 🔒 Security Architecture & How It Works

### 📖 Understanding the Security Flow

The security system in TunnelHub is designed with defense-in-depth principles. Here's a detailed breakdown of how it works:

---

### Step-by-Step Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TUNNELHUB AUTHENTICATION FLOW                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. USER OPENS DASHBOARD                                                    │
│     ┌────────────────┐                                                     │
│     │ Browser: /     │  User navigates to http://localhost:8000            │
│     └────────┬───────┘                                                     │
│              │                                                             │
│  2. PAGE LOADS                                                             │
│              │                                                             │
│     ┌────────▼──────────┐                                                  │
│     │ app.js: init()    │  - Fetches public key from server                │
│     └────────┬──────────┘  - Stores it in state.publicKey                  │
│              │                                                             │
│  3. PUBLIC KEY FETCH                                                       │
│              │                                                             │
│     ┌────────▼──────────┐                                                  │
│     │ GET /api/         │  Server reads from:                              │
│     │ public-key        │    - File: keys/public_key.pem                   │
│     └────────┬──────────┘    - Or: RSA_PUBLIC_KEY env var                  │
│              │              - Or: In-memory storage                        │
│              │                                                             │
│              ▼                                                             │
│     Response: {                                                             │
│       "public_key": "-----BEGIN PUBLIC KEY-----\nMIIB...",                │
│       "key_size": 2048                                                      │
│     }                                                                       │
│                                                                             │
│  4. USER ENTERS PASSWORD                                                   │
│              │                                                             │
│     ┌────────▼──────────┐                                                  │
│     │ User Input        │  User types: admin123                            │
│     └────────┬──────────┘                                                     │
│              │                                                             │
│  5. CLIENT-SIDE ENCRYPTION                                                 │
│              │                                                             │
│     ┌────────▼──────────┐                                                  │
│     │ JSEncrypt Library │  - Uses RSA public key                           │
│     │                  │  - Encrypts password with RSA-PKCS1v15           │
│     └────────┬──────────┘  - Returns Base64-encoded ciphertext            │
│              │                                                             │
│              ▼                                                             │
│     Encrypted: "U2FsdGVkX1+9GmV2h..." (Base64 string)                      │
│                                                                             │
│  ⚠️  NOTE: At this point, the original password is NEVER transmitted!      │
│                                                                             │
│  6. LOGIN REQUEST                                                          │
│              │                                                             │
│     ┌────────▼──────────┐                                                  │
│     │ POST /api/verify  │  Body: { "encrypted_password": "U2Fsd..." }     │
│     └────────┬──────────┘                                                     │
│              │                                                             │
│  7. SERVER-SIDE DECRYPTION                                                 │
│              │                                                             │
│     ┌────────▼──────────┐                                                  │
│     │ security.py:      │  - Loads private key from:                       │
│     │ decrypt_password()│    • File: keys/private_key.pem                 │
│     └────────┬──────────┘    • Or: RSA_PRIVATE_KEY env var                │
│              │              • Or: In-memory storage                        │
│              │                                                             │
│              │  Steps:                                                     │
│              │    1. Base64 decode the ciphertext                          │
│              │    2. Decrypt with RSA private key                          │
│              │    3. Return plaintext password                             │
│              │                                                             │
│              ▼                                                             │
│     Decrypted: "admin123"                                                  │
│                                                                             │
│  8. PASSWORD VERIFICATION                                                  │
│              │                                                             │
│     ┌────────▼──────────┐                                                  │
│     │ security.py:      │  - Uses secrets.compare_digest()                │
│     │ verify_password() │  - Constant-time comparison                      │
│     └────────┬──────────┘  - Prevents timing attacks                       │
│              │                                                             │
│              │  Compares:                                                  │
│              │    decrypted_password == ADMIN_PASSWORD                     │
│              │                                                             │
│  9. SESSION CREATION                                                       │
│              │                                                             │
│     ┌────────▼──────────┐                                                  │
│     │ secrets.token_hex │  - Generates 64 hex characters (256 bits)        │
│     │ (32)              │  - Cryptographically secure random               │
│     └────────┬──────────┘                                                     │
│              │                                                             │
│              ▼                                                             │
│     Session token: "a1b2c3d4e5f6..."                                       │
│                                                                             │
│     ┌──────────────────┐                                                  │
│     │ Sessions Store    │  {                                              │
│     │ (in-memory dict)  │    "a1b2c3...": {                                │
│     └──────────────────┘      "session_token": "a1b2c3...",               │
│                              "is_admin": true,                             │
│                              "created_at": "2025-01-15T10:30:00Z"          │
│                            }                                               │
│                          }                                                 │
│                                                                             │
│ 10. SUCCESS RESPONSE                                                       │
│              │                                                             │
│     ┌────────▼──────────┐                                                  │
│     │ Response to Client │  {                                             │
│     └───────────────────┘    "success": true,                              │
│                             "session_token": "a1b2c3...",                 │
│                             "message": "Login successful"                  │
│                           }                                                 │
│                                                                             │
│ 11. CLIENT STORES SESSION                                                  │
│              │                                                             │
│     ┌────────▼──────────┐                                                  │
│     │ localStorage      │  Stores session token for subsequent requests   │
│     └──────────────────┘  All API calls now include:                       │
│                           Authorization: Bearer a1b2c3...                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 🔐 Why This Design Is Secure

#### 1. **Asymmetric Encryption (RSA)**
- **Public key** can be freely distributed to clients
- **Private key** never leaves the server
- Even if an attacker intercepts the encrypted password, they cannot decrypt it without the private key
- RSA-2048 provides ~112 bits of security (currently unbreakable)

#### 2. **Timing-Attack Resistance**
```python
# ❌ VULNERABLE - String comparison is timing-dependent
if password == stored_password:
    return True

# ✅ SECURE - Constant-time comparison
return secrets.compare_digest(password, stored_password)
```
The `secrets.compare_digest()` function always takes the same amount of time regardless of input, preventing attackers from measuring response times to guess passwords.

#### 3. **Secure Session Tokens**
```python
secrets.token_hex(32)  # 256-bit cryptographically secure random
```
- Uses the operating system's CSPRNG (Cryptographically Secure Pseudo-Random Number Generator)
- 256 bits = 2^256 possible values (impossible to brute force)
- No predictable patterns

#### 4. **Rate Limiting (DoS Protection)**
```python
# Token bucket algorithm
tokens = min(capacity, tokens + elapsed_time * refill_rate)
if tokens < 1:
    return HTTP 429  # Too Many Requests
```
- Prevents brute force attacks on passwords
- Protects against DoS attacks
- Allows bursts while limiting sustained requests

#### 5. **Request Size Validation**
```python
if int(content_length) > MAX_REQUEST_SIZE:
    return HTTP 413  # Request Entity Too Large
```
- Prevents memory exhaustion attacks
- Blocks oversized payloads

---

### 🛡️ Defense Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    DEFENSE IN DEPTH                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LAYER 1: RSA ENCRYPTION                                    │
│  ├─ Passwords encrypted before transmission                │
│  └─ Private key never exposed                               │
│                                                             │
│  LAYER 2: RATE LIMITING                                     │
│  ├─ 120 requests/minute per IP                             │
│  ├─ Request size limits (5MB)                              │
│  └─ Token bucket algorithm                                 │
│                                                             │
│  LAYER 3: SESSION MANAGEMENT                               │
│  ├─ 256-bit secure random tokens                           │
│  ├─ Required for protected endpoints                       │
│  └─ In-memory storage (auto-clear on restart)              │
│                                                             │
│  LAYER 4: PASSWORD VERIFICATION                            │
│  ├─ Constant-time comparison                               │
│  └─ Timing-attack resistant                                │
│                                                             │
│  LAYER 5: API PROTECTION                                    │
│  ├─ Protected endpoints require session token              │
│  ├─ Admin endpoints require password confirmation          │
│  └─ Public endpoints whitelisted                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### 📊 Security Feature Matrix

| Feature | Implementation | Security Benefit |
|---------|---------------|------------------|
| RSA Encryption | 2048-bit PKCS1v15 | Passwords never sent in plaintext |
| Session Tokens | 256-bit secure random | Unforgeable authentication |
| Rate Limiting | Token bucket (120/min) | Prevents brute force & DoS |
| Timing-Safe Compare | `secrets.compare_digest()` | Prevents timing attacks |
| Request Validation | Max 5MB body | Prevents memory exhaustion |
| Key Management | File/Env/Memory | Flexible deployment options |
| Public Endpoint | `/api/public-key` | Safe - no sensitive data |
| Protected Endpoints | Bearer token required | Session-based access control |

---

### ⚠️ Important Security Notes

1. **Private Key Security**: The `keys/private_key.pem` file is the most critical asset. If compromised, an attacker could decrypt passwords. Protect it with:
   - File permissions: `chmod 600 keys/private_key.pem`
   - Never commit to version control
   - Use environment variables in production

2. **HTTPS Required**: While RSA protects passwords, other data (session tokens, tunnel URLs) should still be protected with HTTPS in production.

3. **Session Persistence**: Current implementation uses in-memory sessions. For production with multiple workers, consider Redis for distributed session storage.

4. **No Brute-Force Protection**: Beyond rate limiting, there's no account lockout. Consider adding failed attempt tracking.

### Overview

TunnelHub implements a multi-layered security architecture to protect against common web vulnerabilities and ensure secure communication between clients and the server.

### 1. RSA Encryption Flow

The security system uses **asymmetric encryption** to protect passwords during transmission:

```
┌─────────────────────────────────────────────────────────────────┐
│                    RSA Encryption Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. INITIALIZATION                                              │
│     ┌──────────────┐                                           │
│     │   Server     │  Generates RSA-2048 key pair on startup    │
│     │  Startup     │  - Private key stored securely (server only)│
│     └──────┬───────┘  - Public key sent to frontend             │
│            │                                                     │
│  2. PUBLIC KEY DISTRIBUTION                                     │
│            │                                                     │
│     ┌──────▼──────────┐                                         │
│     │  GET /api/      │  Frontend fetches public key            │
│     │  public-key     │  Response: { public_key: PEM, size: 2048}│
│     └──────┬──────────┘                                         │
│            │                                                     │
│  3. PASSWORD ENCRYPTION (Client-Side)                           │
│            │                                                     │
│     ┌──────▼──────────┐                                         │
│     │   Frontend      │  User enters password                   │
│     │   (JSEncrypt)   │  → Encrypt with RSA public key          │
│     │                 │  → Base64 encode result                 │
│     └──────┬──────────┘                                         │
│            │                                                     │
│  4. AUTHENTICATION REQUEST                                      │
│            │                                                     │
│     ┌──────▼──────────┐                                         │
│     │ POST /api/verify│  Send: { encrypted_password: "base64..." }│
│     └──────┬──────────┘                                         │
│            │                                                     │
│  5. SERVER DECRYPTION                                            │
│            │                                                     │
│     ┌──────▼──────────┐                                         │
│     │   Server        │  Decrypt with private key               │
│     │  (security.py)  │  → Verify against ADMIN_PASSWORD        │
│     │                 │  → Constant-time comparison (timing-safe)│
│     └──────┬──────────┘                                         │
│            │                                                     │
│  6. SESSION CREATION                                            │
│            │                                                     │
│     ┌──────▼──────────┐                                         │
│     │   Session       │  Generate 64-byte hex token (256 bits)  │
     │   Generation     │  Store in-memory: { token, is_admin, created_at }│
│     └─────────────────┘                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Key Management

The [security.py](security.py) module provides flexible key management for different environments:

#### Local Development
```python
# Keys stored in files
keys/
├── private_key.pem  # Server-side only, never exposed
└── public_key.pem   # Sent to frontend for encryption
```

#### Vercel/Serverless Deployment
```python
# Keys stored in environment variables
RSA_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nMIIE..."
RSA_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\nMIIB..."
```

#### In-Memory Mode (Auto-Fallback)
```python
# If file system is unavailable, keys are generated in memory
_in_memory_private_key = None
_in_memory_public_key_pem = None
```

**Key Features:**
- Auto-generation on first run with configurable key size (2048 or 4096-bit)
- Environment variable detection for serverless platforms
- Graceful fallback to in-memory storage
- PKCS8 serialization for private keys
- PEM format for compatibility with JSEncrypt library

### 3. Session Management

**Session Token Generation** ([security.py](security.py):235-242):
```python
def generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_hex(32)  # 256-bit secure random token
```

**Session Storage** ([main.py](main.py):58-59):
```python
# In-memory session storage
sessions: Dict[str, models.SessionData] = {}
```

**Session Verification** ([main.py](main.py):152-159):
```python
async def verify_session(request: Request) -> Optional[models.SessionData]:
    """Verify session token from Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    session_token = auth_header[7:]  # Remove "Bearer " prefix
    return sessions.get(session_token)
```

### 4. Rate Limiting (DoS Protection)

**Token Bucket Algorithm** ([main.py](main.py):97-149):

The middleware implements a token bucket rate limiter:
```python
@app.middleware("http")
async def dos_protection(request: Request, call_next):
    client = request.client.host
    now = time.time()
    refill_per_sec = RATE_LIMIT_RPM / 60.0

    # Refill tokens based on elapsed time
    elapsed = now - entry["last"]
    entry["tokens"] = min(RATE_LIMIT_RPM, entry["tokens"] + elapsed * refill_per_sec)

    # Check if request should be allowed
    if entry["tokens"] < 1.0:
        return JSONResponse(status_code=429, headers={"Retry-After": ...})

    entry["tokens"] -= 1.0
```

**Features:**
- Per-IP rate limiting (configurable, default: 120 req/min)
- Token refill over time (burst tolerance)
- Request size validation (max: 5MB)
- HTTP 429 responses with `Retry-After` header
- Whitelisted endpoints: `/`, `/api/public-key`, `/docs`

### 5. Password Verification

**Constant-Time Comparison** ([security.py](security.py):185-196):
```python
def verify_password(password: str, stored_password: str) -> bool:
    """Verify using constant-time comparison to prevent timing attacks."""
    return secrets.compare_digest(password, stored_password)
```

This prevents timing attacks where an attacker could measure response times to guess passwords character by character.

### 6. Protected Endpoints

**Session Required** ([main.py](main.py):162-172):
```python
def require_session():
    """Decorator to require valid session."""
    async def dependency(request: Request):
        session = await verify_session(request)
        if not session:
            raise HTTPException(status_code=401, detail="Invalid or missing session token")
        return session
    return dependency
```

**Admin Password Required** ([main.py](main.py):175-187):
```python
def require_admin():
    """Decorator to require admin authentication."""
    async def dependency(password: str = None):
        if not secrets.compare_digest(password, ADMIN_PASSWORD):
            raise HTTPException(status_code=401, detail="Invalid admin password")
        return True
    return dependency
```

### 7. Client-Side Security

**JSEncrypt Integration** ([static/js/app.js](static/js/app.js):105-119):
```javascript
function encryptPassword(password) {
    const encrypt = new JSEncrypt();
    encrypt.setPublicKey(state.publicKey);
    const encrypted = encrypt.encrypt(password);
    return encrypted;  // Base64 encoded RSA-encrypted password
}
```

**Secure Headers**:
- All authenticated requests include: `Authorization: Bearer <session_token>`
- Admin operations use: `X-Admin-Password: <password>` (for restart endpoint)

### Security Best Practices

1. ✅ **Change the default admin password** in `.env`
2. ✅ **Use strong ngrok tokens** from your ngrok account
3. ✅ **Don't commit `.env`** or `keys/` directory to version control
4. ✅ **Use HTTPS** in production (reverse proxy with nginx)
5. ✅ **Keep RSA keys private** - never share the `keys/` directory
6. ✅ **Regularly rotate session tokens** (currently cleared on restart)
7. ✅ **Monitor rate limit violations** for potential attacks
8. ✅ **Use strong RSA key sizes** (4096-bit recommended for production)

## 🛠️ API Endpoints

### Authentication

#### `GET /api/public-key`
Get RSA public key for password encryption.

**Response:**
```json
{
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIB...",
  "key_size": 2048
}
```

#### `POST /api/verify`
Verify login credentials with RSA-encrypted password.

**Request:**
```json
{
  "encrypted_password": "base64-encoded-rsa-encrypted-password"
}
```

**Response:**
```json
{
  "success": true,
  "session_token": "a1b2c3d4...",
  "message": "Login successful"
}
```

#### `POST /api/logout`
Logout current session. Requires `Authorization: Bearer <token>` header.

### Tunnel Management

#### `GET /api/tunnels`
Get all tunnels with optional user filtering. Requires authentication.

**Query Parameters:**
- `user_id` (optional): Filter tunnels by user ID

**Response:**
```json
{
  "success": true,
  "tunnels": [
    {
      "id": "tnl_123",
      "public_url": "https://abc123.ngrok.io",
      "proto": "https",
      "region": "us",
      "tunnel_session_id": "sess_456",
      "forwards_to": "http://localhost:3000",
      "created_at": "2025-01-15T10:30:00Z",
      "metadata": {},
      "user_id": "user_1",
      "user_name": "John Doe",
      "custom_name": "My App Tunnel",
      "status": "online"
    }
  ],
  "total_count": 1,
  "filtered_user": null,
  "timestamp": "2025-01-15T10:30:00Z"
}
```

#### `PUT /api/tunnels/{tunnel_id}/name`
Set a custom name for a tunnel. Requires authentication.

**Request:**
```json
{
  "custom_name": "My Custom Tunnel Name"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Custom name updated successfully",
  "tunnel_id": "tnl_123",
  "custom_name": "My Custom Tunnel Name"
}
```

### Admin

#### `GET /api/users`
Get list of all users and their configurations.

**Response:**
```json
{
  "success": true,
  "users": [
    {
      "id": "user_1",
      "name": "John Doe",
      "ngrok_tokens": ["token1", "token2"],
      "ngrok_api_urls": ["https://api.ngrok.com"]
    }
  ],
  "total_count": 1
}
```

#### `GET /api/health`
Server health check with uptime information.

**Response:**
```json
{
  "status": "running",
  "pid": 12345,
  "platform": "linux",
  "uptime_seconds": 3600.5
}
```

#### `POST /api/restart`
Restart the server. Requires admin password in request body.

**Request:**
```json
{
  "password": "admin123"
}
```

### Documentation

- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /api` - API information and endpoint list

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ADMIN_PASSWORD` | Admin password for login | `admin123` | No |
| `RSA_KEY_SIZE` | RSA key size in bits (2048 or 4096) | `2048` | No |
| `USERS` | JSON array of user configurations | `[]` | Yes |
| `AUTO_REFRESH_INTERVAL` | Auto-refresh interval in seconds | `5` | No |
| `RATE_LIMIT_RPM` | Rate limit per minute per IP | `120` | No |
| `MAX_REQUEST_SIZE` | Max request size in bytes (5MB) | `5242880` | No |
| `RSA_PRIVATE_KEY` | Private key for Vercel deployment | `null` | For Vercel |
| `RSA_PUBLIC_KEY` | Public key for Vercel deployment | `null` | For Vercel |

### User Configuration

Each user in the `USERS` array requires:

```json
{
    "id": "unique_user_id",
    "name": "Display Name",
    "ngrok_tokens": ["token1", "token2"],
    "ngrok_api_urls": ["https://api.ngrok.com"]
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (e.g., `user_1`, `john_doe`) |
| `name` | string | Display name shown in the UI |
| `ngrok_tokens` | array | Array of ngrok API tokens for this user |
| `ngrok_api_urls` | array | Ngrok API URLs (default: `["https://api.ngrok.com"]`) |

**Multiple Tokens Per User:**
Each user can have multiple ngrok tokens. The system will fetch tunnels from all tokens sequentially:
```env
USERS='[{"id": "user_1", "name": "John", "ngrok_tokens": ["token1", "token2"], "ngrok_api_urls": ["https://api.ngrok.com"]}]'
```

## 🚀 Production Deployment

### Using Gunicorn

For production, use Gunicorn with Uvicorn workers:

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

### Using systemd (Linux)

Create `/etc/systemd/system/tunnelhub.service`:

```ini
[Unit]
Description=TunnelHub
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/TunnelHub
Environment="PATH=/path/to/TunnelHub/venv/bin"
ExecStart=/path/to/TunnelHub/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 127.0.0.1:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable tunnelhub
sudo systemctl start tunnelhub
sudo systemctl status tunnelhub
```

### Reverse Proxy with nginx

Create `/etc/nginx/sites-available/tunnelhub`:

```nginx
server {
    listen 80;
    server_name tunnelhub.example.com;

    # Redirect HTTP to HTTPS (uncomment after SSL setup)
    # return 301 https://$server_name$request_uri;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Enable and restart nginx:
```bash
sudo ln -s /etc/nginx/sites-available/tunnelhub /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### HTTPS with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d tunnelhub.example.com

# Auto-renewal is configured automatically
```

### Vercel Deployment (Serverless)

TunnelHub supports Vercel serverless deployment:

1. **Generate RSA keys locally:**
```bash
python setup_vercel_keys.py
```

2. **Add keys to Vercel environment variables:**
   - Go to Vercel Dashboard → Your Project → Settings → Environment Variables
   - Add `RSA_PRIVATE_KEY` (copy from script output)
   - Add `RSA_PUBLIC_KEY` (copy from script output)
   - Add `ADMIN_PASSWORD`, `USERS`, etc.

3. **Create `vercel.json`:**
```json
{
  "version": 2,
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}
```

4. **Deploy:**
```bash
vercel deploy
```

### Docker Deployment

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p keys && python -c "from security import ensure_keys_exist; ensure_keys_exist()"

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]
```

Build and run:
```bash
docker build -t tunnelhub .
docker run -p 8000:8000 --env-file .env tunnelhub
```

## 🐛 Troubleshooting

### RSA Keys Not Found

**Error:** "RSA keys not found" or "Public key not found"

**Solutions:**
```bash
# Keys will be auto-generated on first run - just start the server
python main.py

# Or manually generate keys
python security.py

# For Vercel deployment, generate keys locally:
python setup_vercel_keys.py
# Then copy the output to your environment variables
```

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Port Already in Use

**Error:** `OSError: [Errno 48] Address already in use`

**Solutions:**
```bash
# Find and kill the process using port 8000
# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# On Linux/Mac:
lsof -ti:8000 | xargs kill -9

# Or use a different port
python -m uvicorn main:app --port 8080
```

### Tunnels Not Showing

**Possible Causes:**
1. **Invalid ngrok tokens** - Verify tokens are correct and active
2. **No tunnels running** - Ensure ngrok tunnels are actually active on your machine
3. **Network issues** - Check connectivity to ngrok API
4. **Browser errors** - Open browser console (F12) to check for errors

**Debug Steps:**
```bash
# Test ngrok API manually
curl https://api.ngrok.com/tunnels \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Ngrok-Version: 2"

# Check server logs for errors
# Look for "⚠️ Ngrok API error" messages
```

### Rate Limiting Issues

**Error:** HTTP 429 Too Many Requests

**Solution:** Increase rate limit in `.env`:
```env
RATE_LIMIT_RPM=300  # Increase from default 120
```

### Session Not Persisting

**Issue:** Sessions are cleared on server restart

**Reason:** Sessions are stored in-memory for security. This is intentional. For persistent sessions, you would need to implement a database backend (Redis, PostgreSQL, etc.).

### Permission Denied on Keys Directory

**Error:** `PermissionError: [Errno 13] Permission denied: 'keys/private_key.pem'`

**Solutions:**
```bash
# On Linux/Mac - fix permissions
chmod 600 keys/private_key.pem

# Or delete and regenerate keys
rm -rf keys/
python main.py  # Will regenerate automatically
```

## 🔮 Future Enhancements

Planned features (not yet implemented):

- [ ] Tunnel health check endpoint (`GET /api/tunnels/health/{id}`)
- [ ] Delete tunnel functionality via ngrok API
- [ ] Cloudflare tunnel support
- [ ] Create tunnels from UI (via ngrok API)
- [ ] Tunnel usage statistics and analytics
- [ ] Dark mode toggle
- [ ] Multi-language support
- [ ] Persistent sessions (Redis/PostgreSQL backend)
- [ ] User role management (admin vs viewer)
- [ ] WebSocket support for real-time tunnel updates
- [ ] Audit logging for security events
- [ ] Two-factor authentication (2FA)

## 📄 License

This project is provided as-is for educational and commercial use.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

**Development Setup:**
```bash
# Clone repository
git clone https://github.com/yourusername/TunnelHub.git
cd TunnelHub

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py
```

## 🛡️ Security Considerations

### Current Security Features
- ✅ RSA-2048 encryption for password transmission
- ✅ Constant-time password comparison (timing-attack resistant)
- ✅ Secure session token generation (256-bit)
- ✅ Token-bucket rate limiting (DoS protection)
- ✅ Request size validation
- ✅ Session-based authentication

### Recommendations for Production
1. **Use HTTPS** - Never run on plain HTTP in production
2. **Change default password** - Set a strong `ADMIN_PASSWORD`
3. **Enable rate limiting** - Adjust `RATE_LIMIT_RPM` based on your needs
4. **Use firewall rules** - Limit access to trusted IPs only
5. **Monitor logs** - Set up logging and monitoring for security events
6. **Regular updates** - Keep dependencies updated (`pip install -U -r requirements.txt`)
7. **Session timeout** - Consider implementing session expiration
8. **Database sessions** - Use Redis/PostgreSQL for persistent, distributable sessions

### Known Limitations
- ⚠️ Sessions are in-memory (cleared on restart)
- ⚠️ No brute-force protection beyond rate limiting
- ⚠️ No audit logging
- ⚠️ No user roles (all authenticated users have full access)
- ⚠️ No 2FA support

## ⚠️ Disclaimer

This tool is provided for managing ngrok tunnels. Users are responsible for:
- Complying with ngrok's Terms of Service
- Securing their ngrok tokens and admin passwords
- Using this tool legally and ethically
- Any tunnel content accessed through this dashboard
- Implementing additional security measures for production use

---

**Made with ❤️ for the ngrok community**

---

**Made with ❤️ for the ngrok community**
