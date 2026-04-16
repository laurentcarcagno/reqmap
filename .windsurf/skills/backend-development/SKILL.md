---
name: backend-development
description: >
  Designs and implements backend APIs (REST/GraphQL), authentication, authorization,
  validation, error handling, middleware, and server-side business logic.
  Use when creating API routes, securing endpoints, implementing auth flows,
  building server-side business logic, or integrating third-party services.
  NOT for UI components (frontend-development), database schema/migrations
  (database-management), or infrastructure/deployment concerns.
---
# Backend Development Skill

## Dispatch

| Request | Action |
|---------|--------|
| Create / modify API endpoint | → **API Design** + **Validation** |
| Add authentication / authorization | → **Authentication & Authorization** |
| Handle errors / improve resilience | → **Error Handling** + **Resilience** |
| Integrate external service / API | → **External Integrations** |
| Add middleware (logging, rate-limit, CORS) | → **Middleware** |
| Optimize API performance | → **Performance** |
| Empty / ambiguous | Ask for clarification |

---

## 1. API Design

### REST Conventions
| Principle | Rule |
|-----------|------|
| **Resource naming** | Plural nouns, kebab-case: `/api/v1/user-profiles` |
| **HTTP methods** | `GET` = read, `POST` = create, `PUT` = full replace, `PATCH` = partial update, `DELETE` = remove |
| **Status codes** | `200` OK, `201` Created, `204` No Content, `400` Bad Request, `401` Unauthorized, `403` Forbidden, `404` Not Found, `409` Conflict, `422` Unprocessable Entity, `429` Too Many Requests, `500` Internal Server Error |
| **Versioning** | URL prefix: `/api/v1/...`. Increment only on breaking changes. |
| **Pagination** | Cursor-based preferred. Return `{ data, meta: { nextCursor, hasMore } }`. |
| **Filtering & sorting** | Query params: `?status=active&sort=-createdAt` (prefix `-` for descending). |
| **Envelope** | Standard response shape: `{ data, meta?, error? }`. |

### GraphQL Conventions
- Schema-first design. Define `.graphql` schema files, then implement resolvers.
- Use **DataLoader** for N+1 query prevention in every resolver that touches a data source.
- Limit query depth (max 7) and complexity (max 1000) to prevent abuse.
- Mutations return the mutated object + `userErrors[]` array, never throw from resolvers.
- Use input types (`input CreateUserInput`) for all mutations.

### Endpoint File Structure
```
server/
├── routes/
│   ├── auth.routes.ts          # Route definitions + request/response schemas
│   ├── users.routes.ts
│   └── index.ts                # Route aggregation
├── controllers/
│   ├── auth.controller.ts      # Request parsing, response formatting
│   └── users.controller.ts
├── services/
│   ├── auth.service.ts         # Business logic (framework-agnostic)
│   └── users.service.ts
├── repositories/
│   ├── users.repository.ts     # Data access layer (DB queries)
│   └── index.ts
├── middleware/
│   ├── authenticate.ts         # JWT / session verification
│   ├── authorize.ts            # RBAC / permission checks
│   ├── validate.ts             # Schema validation middleware
│   ├── rate-limit.ts           # Rate limiting
│   └── error-handler.ts        # Global error handler
├── schemas/
│   ├── auth.schema.ts          # Zod schemas for auth endpoints
│   └── users.schema.ts
└── utils/
    ├── api-error.ts            # Custom error classes
    ├── logger.ts               # Structured logger
    └── async-handler.ts        # Async error wrapper
```

### Layered Architecture Rules
```
Route → Controller → Service → Repository → Database
         ↓              ↓           ↓
      Validation    Business     Data Access
      + Response     Logic       + Queries
```
- **Routes** define HTTP method, path, middleware chain, and controller handler.
- **Controllers** parse requests, call services, format responses. No business logic here.
- **Services** contain all business logic. Framework-agnostic. Easily testable.
- **Repositories** encapsulate data access. One repository per aggregate/entity. Return domain objects, not raw rows.
- Dependencies flow **inward** only. Services never import from controllers. Repositories never import from services.

---

## 2. Validation

### Schema-First Validation
- Define **Zod schemas** (TypeScript) or **Pydantic models** (Python) for every endpoint's:
  - Request body
  - Query parameters
  - Path parameters
  - Response body (for documentation and runtime safety)

### Validation Middleware Pattern (TypeScript)
```typescript
// validate.ts middleware
import { AnyZodObject, ZodError } from 'zod';

export const validate = (schema: AnyZodObject) =>
  async (req, res, next) => {
    try {
      await schema.parseAsync({
        body: req.body,
        query: req.query,
        params: req.params,
      });
      next();
    } catch (error) {
      if (error instanceof ZodError) {
        return res.status(422).json({
          error: {
            code: 'VALIDATION_ERROR',
            message: 'Invalid request data',
            details: error.errors.map(e => ({
              path: e.path.join('.'),
              message: e.message,
            })),
          },
        });
      }
      next(error);
    }
  };
```

### Rules
- Validate **at the boundary** (middleware), not inside services.
- Reject unknown/extra fields: use `.strict()` on Zod schemas.
- Sanitize string inputs: trim whitespace, normalize Unicode, strip HTML where appropriate.
- Validate file uploads: check MIME type, file size, and extension. Never trust `Content-Type` header alone.

---

## 3. Authentication & Authorization

### Authentication Patterns

| Pattern | Use Case | Implementation |
|---------|----------|----------------|
| **JWT (stateless)** | SPAs, mobile apps, microservices | Short-lived access token (15min) + long-lived refresh token (7d) in httpOnly cookie |
| **Session-based** | Traditional web apps, SSR | Server-side session store (Redis), session ID in httpOnly cookie |
| **OAuth 2.0 + PKCE** | Social login, third-party auth | Authorization Code flow with PKCE for public clients |
| **API keys** | Machine-to-machine, webhooks | Hashed in DB, transmitted via `Authorization: Bearer` or custom header |

### JWT Best Practices
- Sign with **RS256** (asymmetric) for multi-service architectures, **HS256** (symmetric) for single-service.
- Store access tokens in **memory only** (never localStorage). Refresh tokens in **httpOnly, Secure, SameSite=Strict** cookies.
- Include minimal claims: `sub`, `iat`, `exp`, `roles`. Never store sensitive data in JWT payload.
- Implement token rotation: issue new refresh token on each refresh, invalidate the old one.
- Maintain a **token blacklist** (Redis set with TTL) for logout and compromised tokens.

### Authorization: RBAC + Resource-Level

```typescript
// authorize.ts middleware
export const authorize = (...allowedRoles: Role[]) =>
  (req, res, next) => {
    if (!req.user) return res.status(401).json({ error: { code: 'UNAUTHENTICATED' } });
    if (!allowedRoles.includes(req.user.role)) {
      return res.status(403).json({ error: { code: 'FORBIDDEN' } });
    }
    next();
  };

// Resource-level: verify ownership
export const authorizeOwner = (getResourceOwnerId: (req) => Promise<string>) =>
  async (req, res, next) => {
    const ownerId = await getResourceOwnerId(req);
    if (req.user.id !== ownerId && req.user.role !== 'admin') {
      return res.status(403).json({ error: { code: 'FORBIDDEN' } });
    }
    next();
  };
```

### Rules
- **Every protected route** must have both authentication and authorization middleware.
- Check object-level authorization (BOLA prevention): verify the requesting user owns or has access to the specific resource.
- Never expose internal IDs in error messages. Use generic "not found" for unauthorized resource access (prevent enumeration).
- Log all authentication failures with IP, user-agent, and timestamp for audit trails.

---

## 4. Error Handling

### Custom Error Hierarchy
```typescript
export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public code: string,
    message: string,
    public details?: unknown,
    public isOperational = true,
  ) {
    super(message);
    this.name = 'ApiError';
    Error.captureStackTrace(this, this.constructor);
  }

  static badRequest(message: string, details?: unknown) {
    return new ApiError(400, 'BAD_REQUEST', message, details);
  }
  static unauthorized(message = 'Authentication required') {
    return new ApiError(401, 'UNAUTHORIZED', message);
  }
  static forbidden(message = 'Insufficient permissions') {
    return new ApiError(403, 'FORBIDDEN', message);
  }
  static notFound(resource = 'Resource') {
    return new ApiError(404, 'NOT_FOUND', `${resource} not found`);
  }
  static conflict(message: string) {
    return new ApiError(409, 'CONFLICT', message);
  }
  static tooManyRequests(message = 'Rate limit exceeded') {
    return new ApiError(429, 'TOO_MANY_REQUESTS', message);
  }
  static internal(message = 'Internal server error') {
    return new ApiError(500, 'INTERNAL_ERROR', message, undefined, false);
  }
}
```

### Global Error Handler
```typescript
export const errorHandler = (err, req, res, next) => {
  // Operational errors: send to client
  if (err instanceof ApiError && err.isOperational) {
    logger.warn({ err, requestId: req.id }, err.message);
    return res.status(err.statusCode).json({
      error: { code: err.code, message: err.message, details: err.details },
    });
  }
  // Programmer errors: log and send generic 500
  logger.error({ err, requestId: req.id }, 'Unhandled error');
  return res.status(500).json({
    error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' },
  });
};
```

### Rules
- **Never expose stack traces, internal paths, or DB error messages** to the client in production.
- Wrap all async route handlers in `asyncHandler()` to catch unhandled rejections.
- Assign a unique `requestId` (UUID) to every request for log correlation.
- Return consistent error shapes: `{ error: { code: string, message: string, details?: unknown } }`.

---

## 5. Middleware Stack

### Recommended Order (Express / Fastify)
```
1. Request ID (assign UUID)
2. Structured logging (request start)
3. CORS
4. Security headers (Helmet)
5. Body parsing (JSON, URL-encoded, multipart)
6. Rate limiting (per IP, per user, per endpoint)
7. Authentication (JWT / session verification)
8. Authorization (role + resource-level)
9. Validation (schema parsing)
10. Route handler
11. Error handler (global catch-all — always last)
```

### Security Headers (via Helmet)
```typescript
app.use(helmet({
  contentSecurityPolicy: { directives: { defaultSrc: ["'self'"], scriptSrc: ["'self'"] } },
  hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
  referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
  crossOriginEmbedderPolicy: true,
  crossOriginResourcePolicy: { policy: 'same-origin' },
}));
```

### Rate Limiting
```typescript
// Tiered rate limiting
const globalLimiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 100 }); // 100 req / 15min
const authLimiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 10 });   // 10 req / 15min for login
const apiLimiter = rateLimit({ windowMs: 60 * 1000, max: 60 });          // 60 req / min for API
```

---

## 6. Observability & Logging

### Structured Logging (Pino / Winston)
```typescript
// Every log entry includes:
{
  level: 'info',
  timestamp: '2025-01-15T10:30:00.000Z',
  requestId: 'uuid-v4',
  method: 'POST',
  path: '/api/v1/users',
  statusCode: 201,
  duration: 42,          // ms
  userId: 'user-123',    // if authenticated
  message: 'Request completed',
}
```

### Rules
- **Never log** PII (passwords, tokens, SSNs, credit cards). Redact sensitive fields.
- Log at appropriate levels: `error` (broken), `warn` (degraded), `info` (normal operations), `debug` (development).
- Include `requestId`, `userId`, `method`, `path`, `statusCode`, and `duration` in every request log.
- Use log aggregation (e.g., Datadog, Grafana Loki) in staging/production.
- Add health check endpoint: `GET /health` returning `{ status: 'ok', version, uptime }`.

---

## 7. External Integrations

### HTTP Client Rules
- Use a configured HTTP client (Axios instance or `fetch` wrapper) with:
  - Base URL and default headers.
  - Request/response interceptors for logging and error normalization.
  - Timeouts: connect (5s), read (30s). Never leave default (infinite).
  - Retry with exponential backoff (3 attempts, jitter) for 5xx and network errors.
- **Circuit breaker** pattern for critical external dependencies (e.g., payment providers).

### Webhook Handling
- Verify webhook signatures (HMAC-SHA256) before processing.
- Respond with `200` immediately, process asynchronously via a job queue.
- Implement idempotency: store processed webhook IDs to prevent duplicate processing.

---

## 8. Performance

### Techniques
| Technique | When |
|-----------|------|
| **Response caching** (Redis, CDN) | Read-heavy endpoints with stable data |
| **Database query optimization** | Defer to `@database-management` skill |
| **Connection pooling** | Always for DB, Redis, HTTP clients |
| **Compression** (gzip/brotli) | All JSON responses > 1KB |
| **Streaming** | Large file downloads, real-time feeds (SSE) |
| **Background jobs** (BullMQ, Celery) | Email sending, report generation, webhooks |

### Rules
- Set response `Cache-Control` headers explicitly. Default to `no-store` for authenticated endpoints.
- Use ETags for conditional requests on frequently-polled resources.
- Paginate all list endpoints. Maximum page size: 100 items.
- Timeout long-running operations and return `202 Accepted` with a polling URL.

---

## Critical Rules

1. Every endpoint must validate input, authenticate, and authorize before processing.
2. Never expose internal errors, stack traces, or database details to clients.
3. Never store secrets in code. Use environment variables validated at startup.
4. Every async handler must be wrapped to catch unhandled rejections.
5. Every external call must have a timeout and retry strategy.
6. Every mutation must be idempotent or explicitly documented as non-idempotent.
7. Commit only after all tests pass and the linter is clean.
