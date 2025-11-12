# Security Hardening Guide
## Ollama Chat Application - Production Deployment Security

**Version:** 1.1.0
**Last Updated:** November 2025

---

## Table of Contents
1. [Overview](#overview)
2. [Security Checklist](#security-checklist)
3. [CORS Configuration](#cors-configuration)
4. [Error Handling](#error-handling)
5. [Input Validation](#input-validation)
6. [Authentication](#authentication)
7. [Rate Limiting](#rate-limiting)
8. [HTTPS/TLS](#httpstls)
9. [Database Security](#database-security)
10. [Monitoring & Logging](#monitoring--logging)
11. [Deployment Security](#deployment-security)
12. [Common Vulnerabilities](#common-vulnerabilities)

---

## Overview

This guide provides security hardening recommendations for deploying the Ollama Chat Application to production environments. It covers:

- **Network Security**: CORS, HTTPS, authentication
- **Application Security**: Input validation, error handling, logging
- **Infrastructure Security**: Docker, Kubernetes, secrets management
- **Operational Security**: Monitoring, incident response, updates

---

## Security Checklist

### Pre-Deployment (CRITICAL)

- [ ] **CORS Configuration**
  - [ ] Set `CORS_ORIGINS` to specific domains (NOT `*`)
  - [ ] Example: `CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com`
  - [ ] Test with `curl -H "Origin: https://otherdomain.com"`

- [ ] **HTTPS/TLS Setup**
  - [ ] Obtain SSL certificate (Let's Encrypt free option)
  - [ ] Configure Nginx/reverse proxy with HTTPS
  - [ ] Set HSTS header: `Strict-Transport-Security: max-age=31536000`
  - [ ] Redirect HTTP to HTTPS

- [ ] **Secrets Management**
  - [ ] Never commit `.env` file to git
  - [ ] Use environment variables for all secrets
  - [ ] Use Kubernetes Secrets or cloud secrets manager
  - [ ] Rotate secrets regularly

- [ ] **Rate Limiting**
  - [ ] Implement rate limiting (see below)
  - [ ] Set limits: 100 requests/minute per IP
  - [ ] 10 requests/minute for chat endpoint

- [ ] **Authentication** (if user-facing)
  - [ ] Implement API key or OAuth
  - [ ] Never transmit credentials in URLs
  - [ ] Use Bearer tokens over HTTPS

### Post-Deployment (ONGOING)

- [ ] **Monitoring**
  - [ ] Log all API requests and responses
  - [ ] Monitor for suspicious patterns
  - [ ] Set up alerts for errors

- [ ] **Updates**
  - [ ] Keep dependencies updated
  - [ ] Review security advisories weekly
  - [ ] Test updates in staging before production

- [ ] **Backup & Recovery**
  - [ ] Regular backups of conversation data (if stored)
  - [ ] Test recovery procedures
  - [ ] Document incident response procedures

---

## CORS Configuration

### Problem
Overly permissive CORS settings (`allow_origins=["*"]`) allow any website to make requests to your API.

### Solution

**Development (Localhost Only)**
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,OPTIONS
CORS_ALLOW_HEADERS=Content-Type
```

**Production (Specific Domains)**
```bash
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,OPTIONS
CORS_ALLOW_HEADERS=Content-Type,Authorization
```

### Testing
```bash
# This should work (correct origin)
curl -H "Origin: https://yourdomain.com" http://localhost:8000/api/health

# This should be blocked (wrong origin)
curl -H "Origin: https://attacker.com" http://localhost:8000/api/health
```

---

## Error Handling

### Problem
Detailed error messages expose internal implementation details:
- File paths: `/home/user/.ollama/models/tinyllama`
- Stack traces revealing server configuration
- Database connection errors

### Solution
The application uses `sanitize_error_message()` to:

```python
def sanitize_error_message(error: Exception) -> str:
    """
    Returns safe error messages without sensitive details.

    Examples:
    - Input: "Connection refused to /var/run/ollama.sock"
    - Output: "Connection error - service unavailable"

    - Input: "JSONDecodeError: Expecting value at line 1"
    - Output: "Invalid request format"
    """
```

### Best Practices

**DO:**
- ✅ Log full error details server-side
- ✅ Return generic messages to clients
- ✅ Include error codes for debugging
- ✅ Track errors in monitoring system

**DON'T:**
- ❌ Return stack traces to clients
- ❌ Expose file paths or server URLs
- ❌ Leak database connection details
- ❌ Reveal internal configuration

---

## Input Validation

### Message Validation

**Current Implementation** (src/main.py, validate_message function):
```python
# ✅ Length limit: 4000 characters
if len(cleaned) > 4000:
    raise ValueError("Message exceeds maximum length of 4000 characters")

# ✅ Empty message check
if not cleaned:
    raise ValueError("Message cannot be empty")

# ✅ Strip whitespace
cleaned = message.strip()
```

### Future Enhancements

**Consider implementing:**

1. **Content Filtering** (optional based on policy)
   ```python
   # Filter offensive content
   blocked_keywords = ["explicit_content", "spam_pattern"]
   if any(kw in message.lower() for kw in blocked_keywords):
       raise ValueError("Message contains prohibited content")
   ```

2. **Rate Limiting per User**
   ```python
   # Track message volume per IP
   if requests_per_minute[ip] > 100:
       raise HTTPException(status_code=429, detail="Rate limit exceeded")
   ```

3. **Command Injection Prevention**
   ```python
   # Already protected by parameterized Ollama API calls
   # Never use f-strings for shell commands
   ```

---

## Authentication

### Current Implementation
- ✅ No authentication required (local/internal use)
- ✅ Suitable for private networks

### Production Authentication

For user-facing deployments, implement one of:

#### Option 1: API Keys
```python
from fastapi import Header, HTTPException

async def verify_api_key(x_token: str = Header(...)):
    if x_token not in valid_api_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_token

@app.get("/api/chat")
async def chat(request: Request, api_key: str = Depends(verify_api_key)):
    # ... endpoint code
```

#### Option 2: OAuth 2.0
```python
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Verify JWT token
    payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    return payload["sub"]
```

#### Option 3: JWT Tokens
```python
from datetime import datetime, timedelta
import jwt

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt
```

---

## Rate Limiting

### Problem
Without rate limiting, users can overwhelm the service with requests, causing:
- Denial of Service (DoS)
- High resource consumption
- Increased costs

### Solution: Implement Rate Limiting

#### Option 1: Using `slowapi` (Recommended)
```bash
pip install slowapi
```

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/health")
@limiter.limit("100/minute")
async def health_check(request: Request):
    # ... endpoint code
```

#### Option 2: Using `python-ratelimit`
```bash
pip install python-ratelimit
```

```python
from ratelimit import limits, sleep_and_retry
import time

@sleep_and_retry
@limits(calls=100, period=60)  # 100 calls per 60 seconds
async def chat(request: Request):
    # ... endpoint code
```

#### Option 3: Nginx Rate Limiting (Reverse Proxy)
```nginx
# /etc/nginx/nginx.conf
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=chat_limit:10m rate=10r/m;

server {
    location /api/chat {
        limit_req zone=chat_limit burst=5 nodelay;
        proxy_pass http://backend;
    }

    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://backend;
    }
}
```

### Configuration
```bash
# .env configuration for rate limiting
RATE_LIMIT_GENERAL=100/minute
RATE_LIMIT_CHAT=10/minute
RATE_LIMIT_HEALTH=1000/minute
```

---

## HTTPS/TLS

### Obtaining Certificate (Let's Encrypt - Free)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# Certificate location: /etc/letsencrypt/live/yourdomain.com/
```

### Nginx Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL Certificate
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Reverse Proxy
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### Certificate Renewal
```bash
# Automatic renewal (runs twice daily)
sudo certbot renew --quiet

# Manual check
sudo certbot renew --dry-run
```

---

## Database Security

### If Using SQLite (Planned v2.0)

**Secure Configuration:**
```python
# Only readable by application
import os
os.chmod('chat_history.db', 0o600)  # rw-------

# Enable foreign keys and pragma
sqlite3.connect('chat_history.db')
cursor.execute("PRAGMA foreign_keys = ON")
cursor.execute("PRAGMA journal_mode = WAL")  # Write-ahead logging
```

### If Using PostgreSQL (Future)

**Connection Security:**
```python
import psycopg2
from urllib.parse import urlparse

# Use environment variable
db_url = os.getenv("DATABASE_URL")
parsed = urlparse(db_url)

# SSL enforcement
conn = psycopg2.connect(
    host=parsed.hostname,
    user=parsed.username,
    password=parsed.password,
    database=parsed.path.lstrip('/'),
    sslmode='require'  # ← Enforce SSL
)
```

---

## Monitoring & Logging

### Structured Logging

**Current Implementation** (src/main.py):
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

### Recommended: JSON Structured Logging

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

# Apply formatter
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
```

### Key Events to Log

**Security Events:**
```python
# Authentication failures
logger.warning(f"Failed authentication attempt from {remote_ip}")

# Rate limit exceeded
logger.warning(f"Rate limit exceeded for IP {remote_ip}: {requests}/minute")

# Invalid input detected
logger.warning(f"Invalid input from {remote_ip}: {sanitized_input}")

# Configuration errors
logger.error(f"Missing required environment variable: {var_name}")
```

### Monitoring Stack

**Recommended Tools:**
- **Logs**: Elasticsearch/Kibana, Loki, CloudWatch
- **Metrics**: Prometheus, Grafana
- **Tracing**: Jaeger, Datadog
- **Alerting**: AlertManager, PagerDuty

---

## Deployment Security

### Docker Security

**Secure Dockerfile Practice:**

✅ **DO:**
```dockerfile
# Use specific version (not latest)
FROM python:3.11-slim

# Run as non-root user
RUN useradd -m appuser
USER appuser

# Copy application code
COPY --chown=appuser:appuser app /app

# Health check
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8000/api/health
```

❌ **DON'T:**
```dockerfile
# Don't use latest tag
FROM python:latest

# Don't run as root
USER root

# Don't run without health check
```

### Kubernetes Security

**Pod Security Policy:**
```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'MustRunAs'
  fsGroup:
    rule: 'MustRunAs'
  readOnlyRootFilesystem: false
```

**Network Policy:**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
```

### Secrets Management

**Kubernetes Secrets:**
```bash
# Create secret
kubectl create secret generic app-secrets \
  --from-literal=CORS_ORIGINS=https://yourdomain.com \
  --from-literal=DATABASE_URL=postgresql://...

# Reference in deployment
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: chat-app
        env:
        - name: CORS_ORIGINS
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: CORS_ORIGINS
```

**Cloud Secrets Manager:**

AWS Secrets Manager:
```python
import boto3

client = boto3.client('secretsmanager', region_name='us-east-1')
secret = client.get_secret_value(SecretId='ollama-chat/secrets')
cors_origins = secret['SecretString']
```

Google Secret Manager:
```python
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = f"projects/{project_id}/secrets/cors_origins/versions/latest"
response = client.access_secret_version(request={"name": name})
cors_origins = response.payload.data.decode('UTF-8')
```

---

## Common Vulnerabilities

### 1. SQL Injection (if using database)

**Vulnerable:**
```python
# ❌ DON'T DO THIS
query = f"SELECT * FROM users WHERE username = '{username}'"
cursor.execute(query)
```

**Secure:**
```python
# ✅ DO THIS
query = "SELECT * FROM users WHERE username = ?"
cursor.execute(query, (username,))
```

### 2. Cross-Site Scripting (XSS)

**Protected:**
- ✅ Frontend escapes user input automatically
- ✅ No eval() or innerHTML with user data
- ✅ Content-Type: application/json enforced

### 3. Cross-Site Request Forgery (CSRF)

**Already Protected:**
- ✅ State-less API design
- ✅ CORS validation
- ✅ HTTPS-only in production

### 4. Broken Authentication

**Not Applicable (v1.0)** - No authentication required for internal use

**Will Be Important (v2.0+):**
- [ ] Implement strong password hashing (bcrypt)
- [ ] Use JWT with short expiration
- [ ] Implement refresh tokens
- [ ] Add 2FA option

### 5. Broken Access Control

**Current:**
- ✅ No user authentication needed
- ✅ No privileged operations

**Future (v2.0+):**
- [ ] Verify user owns conversation before access
- [ ] Implement role-based access (admin, user)
- [ ] Log all data access

### 6. Sensitive Data Exposure

**Current:**
- ✅ No sensitive data stored in database (v1.0)
- ✅ Error messages sanitized
- ✅ No API keys logged

### 7. Broken Cryptography

**Current:**
- ✅ HTTPS in production
- ✅ TLS 1.2+ enforced
- ✅ No custom crypto implemented

---

## Incident Response

### Suspicious Activity

If you detect suspicious patterns:

1. **Identify**
   ```bash
   # Check logs for unusual activity
   grep "ERROR\|WARNING" application.log | tail -100

   # Check rate limiting
   grep "rate.limit\|429" application.log
   ```

2. **Isolate**
   ```bash
   # Disconnect affected service
   docker-compose down

   # Or block IP in firewall
   sudo iptables -A INPUT -s <attacker_ip> -j DROP
   ```

3. **Investigate**
   ```bash
   # Preserve logs
   cp application.log application.log.backup

   # Check system resources
   top, iostat, netstat
   ```

4. **Remediate**
   ```bash
   # Update vulnerable code
   git pull origin main

   # Rebuild and redeploy
   docker-compose up --build -d
   ```

5. **Communicate**
   - Notify affected users
   - Document incident details
   - Post-mortem analysis

---

## Security Updates

### Weekly Checklist

- [ ] Check for FastAPI security advisories
- [ ] Review Python security updates
- [ ] Check Ollama security announcements
- [ ] Review application logs for errors
- [ ] Test backup and recovery procedures

### Keeping Dependencies Updated

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade fastapi

# Update all packages (carefully!)
pip install -r requirements.txt --upgrade

# Run tests to ensure compatibility
pytest tests/

# Deploy to staging first
docker-compose -f docker-compose.staging.yml up

# Then to production
docker-compose up --build -d
```

---

## Security Resources

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **OWASP API Security**: https://owasp.org/www-project-api-security/
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **Python Security**: https://python.readthedocs.io/en/latest/library/security_warnings.html

---

## Questions?

For security concerns or to report vulnerabilities:
- Review this document again
- Check the main [README.md](../README.md)
- See [CONTRIBUTING.md](../CONTRIBUTING.md) for contact information

---

**Document Status:** ✅ COMPLETE
**Last Updated:** November 2025
**Next Review:** May 2026
