---
name: security-hardening
description: >
  Proactive security assessment and hardening across frontend, backend, and infrastructure.
  Covers OWASP Top 10, dependency auditing, secrets management, CSP, CORS, input sanitization,
  and security headers.
  Use when auditing security posture, hardening endpoints, reviewing auth flows,
  configuring security headers, or responding to vulnerability reports.
  NOT for feature implementation (backend-development), UI work (frontend-development),
  or infrastructure provisioning.
---
# Security Hardening Skill

## Dispatch

| Request | Action |
|---------|--------|
| Security audit / review | → **OWASP Top 10 Checklist** + **Dependency Audit** |
| Fix a vulnerability | → Identify category → relevant section |
| Configure security headers | → **HTTP Security Headers** |
| Secrets management | → **Secrets Management** |
| Input sanitization issue | → **Input Validation & Sanitization** |
| CORS / CSP configuration | → **HTTP Security Headers** |
| Auth security concern | → **Authentication Security** |
| Empty / ambiguous | Ask for clarification |

---

## 1. OWASP Top 10 (2021) — Defense Matrix

| # | Vulnerability | Defense | Verification |
|---|--------------|---------|--------------|
| A01 | **Broken Access Control** | RBAC + resource-level authorization on every endpoint. Deny by default. | Test: access resource as wrong user → 403 |
| A02 | **Cryptographic Failures** | TLS 1.2+ everywhere. AES-256-GCM for data at rest. bcrypt/argon2 for passwords. Never roll custom crypto. | Verify: no plaintext secrets in logs, DB, or client bundles |
| A03 | **Injection** | Parameterized queries (never string interpolation). Zod/Pydantic input validation. CSP for XSS. | Test: SQL injection, XSS payloads in every input field |
| A04 | **Insecure Design** | Threat modeling during design. Rate limiting. Business logic abuse cases in test suite. | Review: abuse scenarios documented and tested |
| A05 | **Security Misconfiguration** | Helmet headers. Disable debug in prod. Remove default credentials. Least-privilege IAM. | Scan: automated header check, port scan |
| A06 | **Vulnerable Components** | `npm audit` / `pip-audit` in CI. Renovate/Dependabot enabled. Pin versions. | Gate: CI fails on critical/high vulnerabilities |
| A07 | **Auth Failures** | MFA support. Account lockout after 5 failures. Secure password reset flow. | Test: brute force, credential stuffing, session fixation |
| A08 | **Data Integrity Failures** | Verify signatures on updates, webhooks, CI/CD artifacts. SRI for CDN scripts. | Verify: all external scripts have `integrity` attributes |
| A09 | **Logging Failures** | Log auth events, access denials, input validation failures. Never log PII. Tamper-proof log storage. | Verify: failed login attempts appear in logs with IP |
| A10 | **SSRF** | Allowlist outbound domains. Block internal IP ranges (10.x, 172.16.x, 192.168.x, 169.254.x). Validate URLs server-side. | Test: attempt to fetch internal metadata endpoints |

---

## 2. HTTP Security Headers

### Required Headers (via Helmet or manual configuration)

```typescript
// Production security headers
{
  // Prevent XSS by controlling resource loading
  'Content-Security-Policy': [
    "default-src 'self'",
    "script-src 'self' 'nonce-{REQUEST_NONCE}'",  // No 'unsafe-inline'
    "style-src 'self' 'unsafe-inline'",             // Tailwind needs this
    "img-src 'self' data: https:",
    "font-src 'self'",
    "connect-src 'self' https://api.example.com",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
  ].join('; '),

  // Force HTTPS for 1 year, including subdomains
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',

  // Prevent MIME type sniffing
  'X-Content-Type-Options': 'nosniff',

  // Control referrer information
  'Referrer-Policy': 'strict-origin-when-cross-origin',

  // Prevent framing (clickjacking)
  'X-Frame-Options': 'DENY',

  // Control browser features
  'Permissions-Policy': 'camera=(), microphone=(), geolocation=(), payment=(self)',

  // Isolate cross-origin resources
  'Cross-Origin-Opener-Policy': 'same-origin',
  'Cross-Origin-Resource-Policy': 'same-origin',
  'Cross-Origin-Embedder-Policy': 'require-corp',
}
```

### CORS Configuration

```typescript
const corsOptions = {
  origin: (origin, callback) => {
    const allowedOrigins = process.env.ALLOWED_ORIGINS?.split(',') ?? [];
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('CORS: Origin not allowed'));
    }
  },
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID'],
  credentials: true,           // Only if cookies/auth needed cross-origin
  maxAge: 86400,               // Preflight cache: 24 hours
  exposedHeaders: ['X-Request-ID', 'X-RateLimit-Remaining'],
};
```

### Rules
- **Never** use `Access-Control-Allow-Origin: *` with `credentials: true`.
- Allowlist specific origins. Never reflect the `Origin` header back without validation.
- Restrict `Access-Control-Allow-Methods` to only the methods your API actually uses.

---

## 3. Input Validation & Sanitization

### Defense in Depth — Three Layers

| Layer | Where | What |
|-------|-------|------|
| **1. Schema validation** | API boundary (middleware) | Zod / Pydantic: type, shape, length, format |
| **2. Business validation** | Service layer | Domain rules: uniqueness, ownership, state transitions |
| **3. Output encoding** | Response / template rendering | HTML encoding, JSON serialization, CSP nonces |

### Input Sanitization Rules
```typescript
// String sanitization pipeline
function sanitizeInput(input: string): string {
  return input
    .trim()                              // Remove leading/trailing whitespace
    .normalize('NFC')                    // Normalize Unicode
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, ''); // Strip control characters
}

// HTML content (user-generated content for display)
// Use DOMPurify server-side or sanitize-html
import DOMPurify from 'isomorphic-dompurify';
const cleanHtml = DOMPurify.sanitize(userHtml, {
  ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li'],
  ALLOWED_ATTR: ['href', 'title'],
});
```

### File Upload Security
- Validate MIME type by reading file magic bytes, not `Content-Type` header.
- Enforce maximum file size (server-side, not just client).
- Generate random filenames. Never use the original filename for storage.
- Store uploads outside the web root or in object storage (S3).
- Scan uploads for malware if accepting executables or archives.
- Serve user uploads from a separate domain / CDN (prevent cookie leakage).

---

## 4. Authentication Security

### Password Handling
```typescript
// Hashing: argon2id (preferred) or bcrypt
import { hash, verify } from '@node-rs/argon2';

const passwordHash = await hash(plaintext, {
  memoryCost: 65536,   // 64 MB
  timeCost: 3,         // 3 iterations
  parallelism: 4,      // 4 threads
});

const isValid = await verify(passwordHash, plaintext);
```

### Password Policy
- Minimum 8 characters. Maximum 128 characters (prevent DoS via hashing).
- Check against breached password databases (Have I Been Pwned API via k-Anonymity).
- No composition rules (uppercase, special char) — they reduce entropy. Encourage passphrases.
- Rate-limit login attempts: 5 failures → 15-minute lockout per account + IP.

### Session Security
| Setting | Value | Purpose |
|---------|-------|---------|
| `httpOnly` | `true` | Prevent JavaScript access to session cookie |
| `secure` | `true` | Cookie only sent over HTTPS |
| `sameSite` | `strict` or `lax` | CSRF protection |
| `maxAge` | 3600 (1 hour) | Session expiry |
| `path` | `/` | Cookie scope |
| `domain` | explicit domain | Prevent subdomain leakage |

### Token Security
- Access tokens: 15 minutes max lifetime. Store in memory only (never localStorage).
- Refresh tokens: 7 days max. Store in httpOnly cookie. Rotate on every use.
- On logout: invalidate refresh token server-side (Redis blacklist with TTL).
- On password change: invalidate ALL existing sessions and tokens.

---

## 5. Secrets Management

### Rules
- **Never** commit secrets to version control. Use `.env` files locally, secret managers in production.
- **Never** log secrets, tokens, or API keys. Redact in error messages.
- **Never** embed secrets in client-side bundles. Verify with `grep` on build output.
- Rotate secrets on a regular schedule (90 days) and immediately on suspected compromise.

### Environment Variable Validation
```typescript
import { z } from 'zod';

const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'staging', 'production']),
  DATABASE_URL: z.string().url(),
  JWT_SECRET: z.string().min(32),
  REDIS_URL: z.string().url(),
  ALLOWED_ORIGINS: z.string().transform(s => s.split(',')),
  SMTP_HOST: z.string().optional(),
});

// Validate at startup — fail fast
export const env = envSchema.parse(process.env);
```

### Pre-commit Hook
```bash
# .husky/pre-commit — prevent secrets from being committed
npx secretlint "**/*"
```

### Scanning
- Use `secretlint` or `gitleaks` as a pre-commit hook AND in CI.
- Scan for: API keys, private keys, connection strings, tokens, passwords in code.
- If a secret is committed: rotate it immediately, force-push to remove from history, run `git filter-repo`.

---

## 6. Dependency Security

### Audit Pipeline
```bash
# JavaScript — run in CI, fail on critical/high
npm audit --audit-level=critical
# or
pnpm audit --audit-level=critical

# Python
pip-audit --strict

# Container images
docker scout cves <image>
trivy image <image>
```

### Rules
- CI pipeline must **fail** on critical or high severity vulnerabilities.
- Review and update dependencies monthly. Maximum age: 6 months behind latest.
- Lock file (`package-lock.json`, `pnpm-lock.yaml`, `poetry.lock`) must always be committed.
- Evaluate new dependencies against: maintenance activity, download count, known vulnerabilities, license, bundle size impact.
- Use Subresource Integrity (SRI) for any scripts loaded from CDNs.

---

## 7. Security Testing

### Automated (CI Pipeline)
| Tool | Purpose | Stage |
|------|---------|-------|
| `eslint-plugin-security` | Static analysis for JS security patterns | Lint |
| `secretlint` / `gitleaks` | Secrets detection | Pre-commit + CI |
| `npm audit` / `pip-audit` | Dependency vulnerabilities | CI |
| `OWASP ZAP` (baseline scan) | Dynamic application security testing | Staging deploy |
| `Playwright` + custom security tests | Auth bypass, IDOR, input injection | E2E |

### Manual Review Triggers
- Any change to authentication or authorization logic.
- Any change to input validation or data serialization.
- Any new external integration or webhook handler.
- Any change to CORS, CSP, or security header configuration.
- Any new file upload or download endpoint.

---

## 8. Incident Response Checklist

When a vulnerability is reported or discovered:

1. **Assess** severity (CVSS score) and blast radius.
2. **Contain** — disable affected feature or block attack vector immediately.
3. **Fix** — patch the root cause, not just the symptom.
4. **Verify** — write a regression test that reproduces the vulnerability and confirms the fix.
5. **Rotate** — rotate any potentially compromised secrets or tokens.
6. **Notify** — inform affected users if data was exposed (legal/compliance requirement).
7. **Document** — add to `model-context.md` as a security decision record.
8. **Prevent** — add automated detection to CI to prevent recurrence.

---

## Critical Rules

1. Never trust client input. Validate and sanitize at every server boundary.
2. Never store passwords in plaintext. Use argon2id or bcrypt only.
3. Never commit secrets to version control. Validate env vars at startup.
4. Never use `Access-Control-Allow-Origin: *` with credentials.
5. Never disable security headers in production for convenience.
6. Never suppress or ignore `npm audit` / `pip-audit` critical findings.
7. Every auth change must be peer-reviewed by a second developer.
8. Every security fix must include a regression test.
