"""
Enterprise-Grade Security Service
Handles authentication, authorization, rate limiting, and input validation
"""

import jwt
import hashlib
import secrets
import time
import re
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import redis
import bcrypt
from pydantic import BaseModel, EmailStr, validator
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
from urllib.parse import urlparse
import ipaddress

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserTier(Enum):
    """User subscription tiers"""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class RateLimitType(Enum):
    """Types of rate limiting"""
    REQUESTS_PER_HOUR = "requests_per_hour"
    REQUESTS_PER_DAY = "requests_per_day"
    CONCURRENT_REQUESTS = "concurrent_requests"
    PAGES_PER_ANALYSIS = "pages_per_analysis"

@dataclass
class RateLimitConfig:
    """Rate limiting configuration per tier"""
    requests_per_hour: int
    requests_per_day: int
    concurrent_requests: int
    max_pages_per_analysis: int
    max_analysis_time: int  # seconds

# Rate limit configurations by tier
RATE_LIMITS = {
    UserTier.FREE: RateLimitConfig(
        requests_per_hour=10,
        requests_per_day=50,
        concurrent_requests=1,
        max_pages_per_analysis=5,
        max_analysis_time=300
    ),
    UserTier.PREMIUM: RateLimitConfig(
        requests_per_hour=100,
        requests_per_day=500,
        concurrent_requests=3,
        max_pages_per_analysis=25,
        max_analysis_time=600
    ),
    UserTier.ENTERPRISE: RateLimitConfig(
        requests_per_hour=1000,
        requests_per_day=5000,
        concurrent_requests=10,
        max_pages_per_analysis=100,
        max_analysis_time=1800
    )
}

class User(BaseModel):
    """User model"""
    user_id: str
    email: EmailStr
    tier: UserTier
    api_key: str
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if len(v) < 32:
            raise ValueError('API key must be at least 32 characters')
        return v

class SecurityRequest(BaseModel):
    """Security-validated request model"""
    url: str
    user_id: str
    tier: UserTier
    request_ip: str
    timestamp: datetime
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        
        parsed = urlparse(v)
        if not parsed.netloc:
            raise ValueError('Invalid URL format')
            
        # Security checks
        if parsed.netloc.lower() in ['localhost', '127.0.0.1', '0.0.0.0']:
            raise ValueError('Localhost URLs are not allowed')
            
        # Check for private IP ranges
        try:
            ip = ipaddress.ip_address(parsed.hostname)
            if ip.is_private or ip.is_loopback:
                raise ValueError('Private IP addresses are not allowed')
        except (ipaddress.AddressValueError, TypeError):
            # It's a domain name, which is fine
            pass
            
        return v

class SecurityService:
    """Comprehensive security service"""
    
    def __init__(self, redis_client: redis.Redis, jwt_secret: str):
        self.redis = redis_client
        self.jwt_secret = jwt_secret
        self.security = HTTPBearer()
        
        # Blocked domains and patterns
        self.blocked_domains = {
            'localhost', '127.0.0.1', '0.0.0.0', 'internal.company.com'
        }
        
        # Suspicious patterns
        self.suspicious_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
            r'onload=',
            r'onerror='
        ]
    
    def generate_api_key(self, user_id: str) -> str:
        """Generate secure API key"""
        timestamp = str(int(time.time()))
        random_bytes = secrets.token_hex(16)
        key_data = f"{user_id}:{timestamp}:{random_bytes}"
        
        # Create hash
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()
        return f"mgx_{key_hash[:32]}"
    
    def generate_jwt_token(self, user: User, expires_hours: int = 24) -> str:
        """Generate JWT token"""
        payload = {
            'user_id': user.user_id,
            'email': user.email,
            'tier': user.tier.value,
            'exp': datetime.utcnow() + timedelta(hours=expires_hours),
            'iat': datetime.utcnow(),
            'iss': 'magentix-api'
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def authenticate_request(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())) -> User:
        """Authenticate incoming request"""
        token = credentials.credentials
        
        # Check if it's an API key or JWT token
        if token.startswith('mgx_'):
            return await self._authenticate_api_key(token)
        else:
            return await self._authenticate_jwt_token(token)
    
    async def _authenticate_api_key(self, api_key: str) -> User:
        """Authenticate using API key"""
        # Get user data from Redis
        user_data = self.redis.get(f"api_key:{api_key}")
        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        import json
        user_dict = json.loads(user_data)
        user = User(**user_dict)
        
        if not user.is_active:
            raise HTTPException(status_code=401, detail="Account deactivated")
        
        # Update last used timestamp
        user.last_used = datetime.utcnow()
        self.redis.setex(f"api_key:{api_key}", 3600*24*30, json.dumps(user.dict(), default=str))
        
        return user
    
    async def _authenticate_jwt_token(self, token: str) -> User:
        """Authenticate using JWT token"""
        payload = self.verify_jwt_token(token)
        
        # Get full user data
        user_data = self.redis.get(f"user:{payload['user_id']}")
        if not user_data:
            raise HTTPException(status_code=401, detail="User not found")
        
        import json
        user_dict = json.loads(user_data)
        return User(**user_dict)
    
    async def check_rate_limits(self, user: User, request_ip: str) -> bool:
        """Check all rate limits for user"""
        config = RATE_LIMITS[user.tier]
        current_time = int(time.time())
        
        # Check requests per hour
        hour_key = f"rate_limit:hour:{user.user_id}:{current_time // 3600}"
        hourly_count = self.redis.get(hour_key) or 0
        if int(hourly_count) >= config.requests_per_hour:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded: {config.requests_per_hour} requests per hour"
            )
        
        # Check requests per day
        day_key = f"rate_limit:day:{user.user_id}:{current_time // 86400}"
        daily_count = self.redis.get(day_key) or 0
        if int(daily_count) >= config.requests_per_day:
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded: {config.requests_per_day} requests per day"
            )
        
        # Check concurrent requests
        concurrent_key = f"concurrent:{user.user_id}"
        concurrent_count = self.redis.get(concurrent_key) or 0
        if int(concurrent_count) >= config.concurrent_requests:
            raise HTTPException(
                status_code=429, 
                detail=f"Too many concurrent requests. Limit: {config.concurrent_requests}"
            )
        
        # Check IP-based rate limiting (additional security)
        ip_key = f"rate_limit:ip:{request_ip}:{current_time // 3600}"
        ip_count = self.redis.get(ip_key) or 0
        if int(ip_count) >= 200:  # Max 200 requests per hour per IP
            raise HTTPException(
                status_code=429, 
                detail="IP rate limit exceeded"
            )
        
        return True
    
    async def increment_rate_limits(self, user: User, request_ip: str):
        """Increment rate limit counters"""
        current_time = int(time.time())
        
        # Increment hourly counter
        hour_key = f"rate_limit:hour:{user.user_id}:{current_time // 3600}"
        pipe = self.redis.pipeline()
        pipe.incr(hour_key)
        pipe.expire(hour_key, 3600)
        
        # Increment daily counter
        day_key = f"rate_limit:day:{user.user_id}:{current_time // 86400}"
        pipe.incr(day_key)
        pipe.expire(day_key, 86400)
        
        # Increment concurrent counter
        concurrent_key = f"concurrent:{user.user_id}"
        pipe.incr(concurrent_key)
        pipe.expire(concurrent_key, 1800)  # 30 minutes
        
        # Increment IP counter
        ip_key = f"rate_limit:ip:{request_ip}:{current_time // 3600}"
        pipe.incr(ip_key)
        pipe.expire(ip_key, 3600)
        
        pipe.execute()
    
    def validate_url_security(self, url: str) -> bool:
        """Comprehensive URL security validation"""
        try:
            parsed = urlparse(url)
            
            # Check protocol
            if parsed.scheme not in ['http', 'https']:
                raise ValueError("Only HTTP and HTTPS protocols are allowed")
            
            # Check domain blacklist
            if parsed.netloc.lower() in self.blocked_domains:
                raise ValueError(f"Domain {parsed.netloc} is not allowed")
            
            # Check for suspicious patterns
            full_url = url.lower()
            for pattern in self.suspicious_patterns:
                if re.search(pattern, full_url, re.IGNORECASE):
                    raise ValueError("URL contains suspicious patterns")
            
            # Check URL length
            if len(url) > 2048:
                raise ValueError("URL too long")
            
            # Check for private IP addresses
            try:
                ip = ipaddress.ip_address(parsed.hostname)
                if ip.is_private or ip.is_loopback or ip.is_multicast:
                    raise ValueError("Private/local IP addresses are not allowed")
            except (ipaddress.AddressValueError, TypeError):
                # It's a domain name, additional checks
                if parsed.hostname and ('internal' in parsed.hostname.lower() or 
                                      'localhost' in parsed.hostname.lower()):
                    raise ValueError("Internal domains are not allowed")
            
            return True
            
        except Exception as e:
            logger.warning(f"URL validation failed for {url}: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid URL: {str(e)}")
    
    def sanitize_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data to prevent injection attacks"""
        sanitized = {}
        
        for key, value in input_data.items():
            if isinstance(value, str):
                # Remove potentially dangerous characters
                sanitized_value = re.sub(r'[<>"\';()&+]', '', value)
                sanitized_value = sanitized_value.strip()
                sanitized[key] = sanitized_value
            else:
                sanitized[key] = value
        
        return sanitized
    
    async def log_security_event(self, event_type: str, user_id: str, details: Dict[str, Any]):
        """Log security events for monitoring"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'details': details
        }
        
        # Store in Redis with expiration
        log_key = f"security_log:{int(time.time())}:{secrets.token_hex(8)}"
        self.redis.setex(log_key, 86400*7, str(log_entry))  # Keep for 7 days
        
        # Also log to application logs
        logger.info(f"Security Event: {event_type} - User: {user_id} - Details: {details}")
    
    def get_user_rate_limit_status(self, user: User) -> Dict[str, Any]:
        """Get current rate limit status for user"""
        config = RATE_LIMITS[user.tier]
        current_time = int(time.time())
        
        # Get current counters
        hour_key = f"rate_limit:hour:{user.user_id}:{current_time // 3600}"
        day_key = f"rate_limit:day:{user.user_id}:{current_time // 86400}"
        concurrent_key = f"concurrent:{user.user_id}"
        
        hourly_used = int(self.redis.get(hour_key) or 0)
        daily_used = int(self.redis.get(day_key) or 0)
        concurrent_used = int(self.redis.get(concurrent_key) or 0)
        
        return {
            'tier': user.tier.value,
            'limits': {
                'requests_per_hour': config.requests_per_hour,
                'requests_per_day': config.requests_per_day,
                'concurrent_requests': config.concurrent_requests,
                'max_pages_per_analysis': config.max_pages_per_analysis
            },
            'usage': {
                'hourly_used': hourly_used,
                'daily_used': daily_used,
                'concurrent_used': concurrent_used
            },
            'remaining': {
                'hourly_remaining': max(0, config.requests_per_hour - hourly_used),
                'daily_remaining': max(0, config.requests_per_day - daily_used),
                'concurrent_available': max(0, config.concurrent_requests - concurrent_used)
            }
        }

class SecurityMiddleware:
    """Security middleware for FastAPI"""
    
    def __init__(self, security_service: SecurityService):
        self.security_service = security_service
    
    async def __call__(self, request: Request, call_next):
        """Process security checks"""
        start_time = time.time()
        
        # Get client IP
        client_ip = request.client.host
        if 'x-forwarded-for' in request.headers:
            client_ip = request.headers['x-forwarded-for'].split(',')[0].strip()
        
        # Log request
        logger.info(f"Request from {client_ip}: {request.method} {request.url}")
        
        # Process request
        response = await call_next(request)
        
        # Log response time
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response

# Factory functions
def create_security_service(redis_client: redis.Redis, jwt_secret: str) -> SecurityService:
    """Factory function to create security service"""
    return SecurityService(redis_client, jwt_secret)

def create_test_user(security_service: SecurityService, email: str, tier: UserTier) -> User:
    """Create a test user (for development/testing)"""
    user_id = hashlib.md5(email.encode()).hexdigest()[:16]
    api_key = security_service.generate_api_key(user_id)
    
    user = User(
        user_id=user_id,
        email=email,
        tier=tier,
        api_key=api_key,
        created_at=datetime.utcnow(),
        is_active=True
    )
    
    # Store in Redis
    import json
    security_service.redis.setex(f"api_key:{api_key}", 86400*30, json.dumps(user.dict(), default=str))
    security_service.redis.setex(f"user:{user_id}", 86400*30, json.dumps(user.dict(), default=str))
    
    return user

# Example usage
if __name__ == "__main__":
    import redis
    
    # Initialize Redis client
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    # Create security service
    security_service = create_security_service(redis_client, "your-super-secret-jwt-key")
    
    # Create test users
    free_user = create_test_user(security_service, "user@example.com", UserTier.FREE)
    premium_user = create_test_user(security_service, "premium@example.com", UserTier.PREMIUM)
    
    print(f"Free user API key: {free_user.api_key}")
    print(f"Premium user API key: {premium_user.api_key}")
    
    # Test URL validation
    try:
        security_service.validate_url_security("https://technioz.com")
        print("URL validation passed")
    except HTTPException as e:
        print(f"URL validation failed: {e.detail}")
