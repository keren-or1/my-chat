# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability, **please do not open a public issue**. Instead:

1. **Email** the maintainers at [security contact]
2. **Include:**
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

3. **Timeline:**
   - We will acknowledge receipt within 48 hours
   - We aim to release a fix within 7 days for critical issues
   - We will credit you in the security advisory

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.1.x   | ✅ Yes    |
| 1.0.x   | ✅ Yes    |
| < 1.0   | ❌ No     |

## Security Best Practices

When using the Ollama Chat Application:

### 1. API Keys & Secrets
- ✅ Use environment variables for sensitive data
- ✅ Never hardcode secrets in code
- ❌ Don't commit `.env` files
- ✅ Use `.env.example` for templates

### 2. Input Validation
- ✅ All inputs are sanitized
- ✅ Message length limited to 4000 characters
- ✅ Invalid JSON rejected
- ✅ XSS prevention implemented

### 3. Network Security
- ✅ CORS configured for your domain only
- ✅ HTTPS recommended for production
- ✅ Rate limiting available via plugins
- ✅ Input/output validation on all endpoints

### 4. Data Privacy
- ✅ No external API calls (local only)
- ✅ No data logging by default
- ✅ Conversation history local-only
- ✅ No telemetry or tracking

### 5. Dependency Security
- ✅ Regular dependency updates
- ✅ Vulnerability scanning in CI/CD
- ✅ Minimal dependencies (only what's needed)
- ✅ No untrusted packages

## Security Checklist for Deployment

- [ ] Use strong, unique API keys
- [ ] Run behind a reverse proxy (nginx, Apache)
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Keep Ollama service updated
- [ ] Run application as non-root user
- [ ] Configure firewall rules
- [ ] Set up rate limiting
- [ ] Enable access logging
- [ ] Regular security patches
- [ ] Monitor for suspicious activity

## Vulnerability Disclosure Format

When we issue a security fix, we will:

1. Release a patch version
2. Publish a security advisory
3. Credit the reporter
4. Provide migration guidance

Example advisory:
```
[SECURITY] Fixed XSS vulnerability in chat input (CVE-2024-XXXXX)
- Description: Input sanitization bypass
- Severity: Medium
- Affected versions: < 1.1.2
- Fix: Update to 1.1.2 or later
```

## Third-Party Dependencies

Security-critical dependencies:
- `fastapi`: Web framework (actively maintained)
- `requests`: HTTP client (actively maintained)
- `pydantic`: Data validation (actively maintained)

All dependencies are:
- Regularly updated
- Scanned for vulnerabilities
- Tested before release

## OWASP Top 10 Mitigation

| Risk | Mitigation |
|------|-----------|
| Injection | Input validation, parameterized queries |
| Broken Auth | No auth required (local only) |
| Sensitive Data | No PII stored, local-only |
| XML External Entities | JSON only, no XML parsing |
| Broken Access Control | Single-user system |
| Security Misconfiguration | Secure defaults, env config |
| XSS | Input sanitization, output encoding |
| Insecure Deserialization | No untrusted serialization |
| Using Components with Known Vuln | Dependency scanning |
| Insufficient Logging | Comprehensive logging available |

---

**Last Updated:** November 2025  
**Version:** 1.0  
**Maintainers:** Tal & Keren
