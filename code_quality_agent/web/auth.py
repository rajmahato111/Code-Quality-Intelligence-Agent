"""Authentication and rate limiting for the web API."""

import time
import hashlib
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging

from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# JWT is optional for this implementation
try:
    import jwt
except ImportError:
    jwt = None

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for the identifier."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        user_requests = self.requests[identifier]
        while user_requests and user_requests[0] < window_start:
            user_requests.popleft()
        
        # Check if under limit
        if len(user_requests) >= self.max_requests:
            return False
        
        # Add current request
        user_requests.append(now)
        return True
    
    def get_reset_time(self, identifier: str) -> float:
        """Get time when rate limit resets for identifier."""
        user_requests = self.requests[identifier]
        if not user_requests:
            return time.time()
        return user_requests[0] + self.window_seconds


class APIKeyManager:
    """Simple API key management."""
    
    def __init__(self):
        """Initialize API key manager."""
        self.api_keys = {}  # key -> user_info
        self.sessions = {}  # session_id -> session_info
    
    def generate_api_key(self, user_id: str, permissions: Optional[Dict[str, Any]] = None) -> str:
        """Generate a new API key for a user."""
        api_key = secrets.token_urlsafe(32)
        self.api_keys[api_key] = {
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'permissions': permissions or {},
            'last_used': None,
            'usage_count': 0
        }
        logger.info(f"Generated API key for user: {user_id}")
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key and return user info."""
        if api_key not in self.api_keys:
            return None
        
        user_info = self.api_keys[api_key]
        user_info['last_used'] = datetime.utcnow()
        user_info['usage_count'] += 1
        
        return user_info
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            logger.info(f"Revoked API key: {api_key[:8]}...")
            return True
        return False
    
    def create_session(self, user_id: Optional[str] = None) -> str:
        """Create a new session."""
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.utcnow(),
            'last_activity': datetime.utcnow(),
            'analysis_jobs': [],
            'preferences': {}
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        session['last_activity'] = datetime.utcnow()
        return session
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24):
        """Clean up expired sessions."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        expired_sessions = [
            sid for sid, session in self.sessions.items()
            if session['last_activity'] < cutoff
        ]
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")


# Global instances
rate_limiter = RateLimiter(max_requests=1000, window_seconds=3600)  # 1000 requests per hour
api_key_manager = APIKeyManager()
security = HTTPBearer(auto_error=False)


def get_client_identifier(request: Request) -> str:
    """Get client identifier for rate limiting."""
    # Try to get real IP from headers (for reverse proxy setups)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    # Fallback to direct client IP
    return request.client.host if request.client else 'unknown'


def check_rate_limit(request: Request):
    """Check rate limit for the request."""
    client_id = get_client_identifier(request)
    
    if not rate_limiter.is_allowed(client_id):
        reset_time = rate_limiter.get_reset_time(client_id)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(rate_limiter.max_requests),
                "X-RateLimit-Reset": str(int(reset_time))
            }
        )


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    """Get current user from API key or session."""
    
    # Check for API key in Authorization header
    if credentials:
        api_key = credentials.credentials
        user_info = api_key_manager.validate_api_key(api_key)
        if user_info:
            return user_info
    
    # Check for API key in query parameter (for development)
    api_key = request.query_params.get('api_key')
    if api_key:
        user_info = api_key_manager.validate_api_key(api_key)
        if user_info:
            return user_info
    
    # Check for session cookie
    session_id = request.cookies.get('session_id')
    if session_id:
        session_info = api_key_manager.get_session(session_id)
        if session_info:
            return {'session': session_info, 'user_id': session_info.get('user_id')}
    
    # Return anonymous user
    return {'user_id': None, 'anonymous': True}


def require_authentication(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require authentication for the endpoint."""
    if current_user.get('anonymous'):
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return current_user


def require_permission(permission: str):
    """Decorator to require specific permission."""
    def permission_checker(current_user: Dict[str, Any] = Depends(require_authentication)):
        permissions = current_user.get('permissions', {})
        if not permissions.get(permission, False):
            raise HTTPException(
                status_code=403,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker


class SecurityHeaders:
    """Security headers middleware."""
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to response."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self'"
        )
        return response


def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for logging."""
    return hashlib.sha256(data.encode()).hexdigest()[:8]


def create_demo_api_key() -> str:
    """Create a demo API key for testing."""
    demo_key = api_key_manager.generate_api_key(
        user_id="demo_user",
        permissions={
            "analyze_repository": True,
            "ask_questions": True,
            "view_results": True
        }
    )
    logger.info(f"Created demo API key: {demo_key}")
    return demo_key