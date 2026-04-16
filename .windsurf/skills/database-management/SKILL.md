---
name: database-management
description: >
  Manages database schema design, migrations, indexing, query optimization,
  data integrity, ORM configuration, and connection management.
  Use when designing tables, writing migrations, optimizing queries, configuring
  ORMs (Prisma, Drizzle, SQLAlchemy), or troubleshooting data integrity issues.
  NOT for API route logic (backend-development), UI components (frontend-development),
  or infrastructure provisioning.
---
# Database Management Skill

## Dispatch

| Request | Action |
|---------|--------|
| Design a new table / schema | → **Schema Design** |
| Create or modify a migration | → **Migrations** |
| Optimize a slow query | → **Query Optimization** |
| Add / review indexes | → **Indexing Strategy** |
| Fix data integrity issue | → **Data Integrity** |
| Configure ORM / connection pooling | → **ORM & Connection Management** |
| Seed data / fixtures | → **Seeding** |
| Empty / ambiguous | Ask for clarification |

---

## 1. Schema Design

### Relational Modeling Principles

| Principle | Rule |
|-----------|------|
| **Normalize to 3NF** | Default for OLTP workloads. Every non-key column depends on the key, the whole key, and nothing but the key. |
| **Strategic denormalization** | Allowed for read-heavy queries with measured performance needs. Document the trade-off in a comment. |
| **Naming conventions** | Tables: `snake_case`, plural (`user_profiles`). Columns: `snake_case`, singular (`first_name`). |
| **Primary keys** | Use `UUID v7` (time-sortable) or `CUID2` for distributed systems. Auto-increment `BIGINT` for single-DB setups. |
| **Timestamps** | Every table must have `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()` and `updated_at TIMESTAMPTZ NOT NULL`. |
| **Soft deletes** | Use `deleted_at TIMESTAMPTZ NULL` when business rules require audit trails. Add a partial index on `deleted_at IS NULL`. |

### Data Type Selection

| Data | Correct Type | Avoid |
|------|-------------|-------|
| Money / currency | `DECIMAL(19,4)` or integer cents | `FLOAT`, `DOUBLE` |
| Email, URL | `VARCHAR(320)`, `TEXT` with CHECK | Unbounded `TEXT` without validation |
| Status / enum | `VARCHAR` with CHECK constraint or DB enum type | Magic integers |
| JSON documents | `JSONB` (Postgres) | `TEXT` storing JSON strings |
| Boolean flags | `BOOLEAN NOT NULL DEFAULT false` | `SMALLINT` 0/1 |
| IP addresses | `INET` (Postgres) or `VARCHAR(45)` | `INTEGER` |
| Dates (no time) | `DATE` | `TIMESTAMPTZ` |
| Timestamps | `TIMESTAMPTZ` (always with timezone) | `TIMESTAMP` (without TZ) |

### Relationship Patterns

```sql
-- One-to-Many: Foreign key on the "many" side
ALTER TABLE orders ADD COLUMN user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE;

-- Many-to-Many: Junction table with composite primary key
CREATE TABLE user_roles (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (user_id, role_id)
);

-- One-to-One: Unique foreign key
ALTER TABLE user_profiles ADD COLUMN user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE;
```

### Constraints Checklist
- [ ] `NOT NULL` on all required fields (default stance: NOT NULL unless genuinely optional).
- [ ] `UNIQUE` constraints on natural keys (email, username, slug).
- [ ] `CHECK` constraints for domain validation (`CHECK (price >= 0)`, `CHECK (status IN ('active','inactive'))`).
- [ ] `FOREIGN KEY` with explicit `ON DELETE` action (`CASCADE`, `SET NULL`, or `RESTRICT`).
- [ ] Composite unique constraints where business rules demand uniqueness across multiple columns.

---

## 2. Migrations

### Principles
- **Deterministic:** Every migration produces the same result regardless of when it runs.
- **Reversible:** Every `up` migration has a corresponding `down` migration. Test both directions.
- **Atomic:** One logical schema change per migration file. Never mix data migrations with schema changes.
- **Forward-only in production:** Rollbacks via new forward migrations, not by running `down`.

### Migration File Naming
```
YYYYMMDDHHMMSS_<descriptive_name>.sql
# Example: 20250315143000_add_user_profiles_table.sql
```

### Workflow
1. **Design** the schema change (consult Schema Design section).
2. **Generate** the migration: `npx prisma migrate dev --name <name>` or `alembic revision --autogenerate -m "<name>"`.
3. **Review** the generated SQL. Never blindly trust auto-generated migrations.
4. **Test locally:** run `up`, verify schema, run `down`, verify rollback.
5. **Test with seed data:** ensure existing data is compatible with the migration.
6. **Commit** the migration file alongside the code that depends on it.

### Dangerous Operations Checklist
| Operation | Risk | Mitigation |
|-----------|------|------------|
| Drop column | Data loss | Ensure column is unused in code for ≥1 release before dropping |
| Rename column | Breaks queries | Use two-phase: add new → backfill → update code → drop old |
| Add NOT NULL | Fails on existing NULLs | Add with DEFAULT, or backfill first, then add constraint |
| Add index on large table | Table lock | Use `CREATE INDEX CONCURRENTLY` (Postgres) |
| Change column type | Data truncation | Test with production-like data volume |

---

## 3. Indexing Strategy

### When to Index
- Columns frequently used in `WHERE` clauses.
- Columns used in `JOIN` conditions.
- Columns used in `ORDER BY` / `GROUP BY`.
- Foreign key columns (always index these).
- Columns with high cardinality used in equality checks.

### Index Types (PostgreSQL)

| Type | Use Case |
|------|----------|
| **B-tree** (default) | Equality and range queries (`=`, `<`, `>`, `BETWEEN`) |
| **GIN** | Full-text search, JSONB containment (`@>`), array membership |
| **GiST** | Geospatial queries, range types, nearest-neighbor |
| **Partial index** | Queries filtering on a specific condition (`WHERE deleted_at IS NULL`) |
| **Composite index** | Multi-column queries (leftmost prefix rule applies) |
| **Unique index** | Enforce uniqueness (prefer over UNIQUE constraint when you need partial uniqueness) |

### Composite Index Column Order
```
-- For query: WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC
-- Index order: equality columns first, then range/sort columns
CREATE INDEX idx_orders_tenant_status_created 
  ON orders (tenant_id, status, created_at DESC);
```

### Anti-Patterns
- Never index columns with very low cardinality alone (e.g., boolean `is_active` with 50/50 distribution).
- Never create redundant indexes (index on `(a, b)` already covers queries on `(a)`).
- Don't over-index: each index slows writes. Aim for the minimum set that covers critical query patterns.
- Review unused indexes quarterly: `pg_stat_user_indexes` → `idx_scan = 0`.

---

## 4. Query Optimization

### Diagnostic Workflow
1. **Identify** slow queries from application logs or `pg_stat_statements`.
2. **Analyze** with `EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)`.
3. **Look for:** sequential scans on large tables, nested loop joins without indexes, high buffer reads.
4. **Fix** by adding indexes, rewriting the query, or denormalizing.
5. **Verify** improvement with before/after `EXPLAIN ANALYZE` comparison.

### Common Optimizations

| Problem | Solution |
|---------|----------|
| N+1 queries | Use eager loading (`include` in Prisma, `joinedload` in SQLAlchemy) |
| Sequential scan on large table | Add appropriate index (see Indexing Strategy) |
| Slow COUNT on large table | Use approximate counts (`reltuples` from `pg_class`) for UI |
| Expensive JOIN | Verify join columns are indexed. Consider materialized view for complex aggregations. |
| Slow LIKE '%term%' | Use trigram index (`pg_trgm`) or full-text search (`tsvector`) |
| Large result sets | Always paginate. Use cursor-based pagination for stable results. |

### Pagination Patterns

```sql
-- Cursor-based (preferred): stable, performant
SELECT * FROM orders
WHERE created_at < :cursor_timestamp
ORDER BY created_at DESC
LIMIT 20;

-- Offset-based (simple, but slow for deep pages):
SELECT * FROM orders
ORDER BY created_at DESC
LIMIT 20 OFFSET 100;
```

---

## 5. Data Integrity

### Transaction Patterns
```typescript
// Prisma interactive transaction
const result = await prisma.$transaction(async (tx) => {
  const order = await tx.order.create({ data: orderData });
  await tx.inventory.update({
    where: { productId: order.productId },
    data: { quantity: { decrement: order.quantity } },
  });
  if (updatedInventory.quantity < 0) {
    throw new Error('Insufficient inventory'); // Rolls back entire transaction
  }
  return order;
});
```

### Rules
- **All multi-table mutations** must be wrapped in a transaction.
- Use `SERIALIZABLE` isolation for financial operations; `READ COMMITTED` (default) for most others.
- Handle deadlocks gracefully: retry with exponential backoff (max 3 attempts).
- **Optimistic locking:** use a `version` column or `updated_at` check for concurrent updates.
- **Never** perform external side effects (email, API calls) inside a transaction. Do them after commit.

### Backup & Recovery
- Automate daily backups with point-in-time recovery (PITR) enabled.
- Test restore procedures quarterly. An untested backup is not a backup.
- For destructive migrations: take a manual backup snapshot before applying.

---

## 6. ORM & Connection Management

### Prisma (TypeScript)
```typescript
// prisma/schema.prisma — best practices
generator client {
  provider        = "prisma-client-js"
  previewFeatures = ["fullTextSearch", "metrics"]
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String
  role      Role     @default(MEMBER)
  posts     Post[]
  createdAt DateTime @default(now()) @map("created_at")
  updatedAt DateTime @updatedAt @map("updated_at")

  @@map("users")
}
```

### Drizzle ORM (TypeScript — Alternative)
```typescript
export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  email: varchar('email', { length: 320 }).notNull().unique(),
  name: varchar('name', { length: 255 }).notNull(),
  role: roleEnum('role').notNull().default('member'),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).notNull().defaultNow(),
});
```

### Connection Pooling
| Setting | Development | Production |
|---------|------------|------------|
| Pool size | 5 | `CPU cores × 2 + 1` (start with 20) |
| Idle timeout | 30s | 10s |
| Connection timeout | 10s | 5s |
| Statement timeout | 30s | 10s |

### Rules
- Use a **single Prisma/Drizzle client instance** (singleton pattern). Never create per-request clients.
- Always use parameterized queries. Never interpolate user input into SQL strings.
- Close connections on application shutdown (`prisma.$disconnect()`, pool `end()`).
- Use connection poolers (PgBouncer, Supabase pooler) for serverless environments.

---

## 7. Seeding

### Principles
- Seed scripts must be **idempotent** (safe to run multiple times).
- Use `upsert` operations keyed on natural identifiers (email, slug), not generated IDs.
- Separate seed data by purpose: `seed-dev.ts` (rich development data), `seed-test.ts` (minimal fixtures), `seed-prod.ts` (reference data only: roles, permissions, config).
- Never seed production with test data.

---

## Critical Rules

1. Every table must have a primary key, `created_at`, and `updated_at`.
2. Every foreign key column must be indexed.
3. Every migration must be reversible and tested in both directions before commit.
4. Never use raw string interpolation in queries. Always parameterize.
5. Never perform side effects inside database transactions.
6. Every schema change must be reviewed for its impact on existing data and indexes.
7. Commit migrations alongside the application code that depends on them.
