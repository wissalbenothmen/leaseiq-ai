# Security

## Posture

| Control | Implementation |
|---|---|
| Password hashing | bcrypt via passlib |
| Session auth | JWT HS256, 8h default expiry, signed with `SECRET_KEY` |
| Secret strength | `config.py:validate_secret_key` rejects keys < 32 chars or in the weak-key blocklist |
| Transport | HSTS header (`max-age=63072000; includeSubDomains; preload`) |
| Click-jacking | `X-Frame-Options: DENY` |
| MIME sniffing | `X-Content-Type-Options: nosniff` |
| Referer leakage | `Referrer-Policy: strict-origin-when-cross-origin` |
| Permissions | `Permissions-Policy: geolocation=(), microphone=(), camera=()` |
| Caching | `Cache-Control: no-store` on all API responses |
| CORS | Allow-list driven by `ALLOWED_ORIGINS` |
| Rate limiting | slowapi — default 120 req/min, configurable per route |
| Audit trail | Every mutating route calls `audit_service.log_action()` |
| Request tracing | `X-Request-ID` header on every request + log line |

## Known gaps (roadmap)

| Gap | Plan |
|---|---|
| No refresh tokens — users get kicked out after access-token expiry | Add rotating refresh tokens, store in httpOnly cookies |
| JWT in localStorage (XSS-vulnerable) | Move to httpOnly cookies with the refresh-token rollout |
| No MFA | Add TOTP MFA via pyotp after multi-tenancy |
| Single-tenant schema | Add `organization_id` columns + Postgres row-level security |
| No password reset flow | Email-based reset with one-time token |
| No CSP header | Add a Content-Security-Policy tuned for the React SPA |

## Reporting a vulnerability

Email security disclosures privately to **security@example.com** (replace with your address before going live). Please include reproduction steps and impact.

We aim to acknowledge within 2 business days and ship a fix within 30 days for critical issues. Do not file public GitHub issues for security problems.
