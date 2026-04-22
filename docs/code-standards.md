# Code Standards & Conventions

**Last Updated:** 2026-04-21

## General Principles

- **YAGNI** — You Aren't Gonna Need It; don't implement speculative features
- **KISS** — Keep It Simple, Stupid; prefer straightforward solutions
- **DRY** — Don't Repeat Yourself; extract reusable logic into shared modules
- **Readability First** — Code is read more often than written; optimize for clarity

## File Organization

### Naming Conventions

| Type | Convention | Example |
|------|-----------|---------|
| Python files | snake_case | `auth_service.py`, `user_models.py` |
| TypeScript files | kebab-case | `auth-api.ts`, `chat-message.tsx` |
| Python functions | snake_case | `get_user_by_email()`, `embed_text()` |
| Python classes | PascalCase | `UserService`, `DocumentChunk` |
| TypeScript functions | camelCase | `getUserById()`, `embedText()` |
| TypeScript interfaces | PascalCase | `User`, `DocumentResponse` |
| Python constants | UPPER_SNAKE_CASE | `DEFAULT_CHUNK_SIZE`, `MAX_FILE_SIZE` |
| Python private | _leading_underscore | `_validate_token()` |

### File Size Limit

**Maximum 200 lines per code file** (excluding tests, config, migrations).

**When to split:**
- File exceeds 200 lines → extract logic into separate module
- Too many responsibilities → split by domain (e.g., `auth_service.py` vs `auth_schemas.py`)
- Reusable utilities → move to `lib/` or `utils/`

## Backend (Python 3.11+)

### Dependencies

**Core:**
- FastAPI 0.111.0 — web framework
- SQLAlchemy 2.0.30 — ORM (async mode)
- Pydantic 2.7 — data validation
- asyncpg 0.29.0 — async PostgreSQL driver
- pgvector 0.3.0 — vector database support

**Processing:**
- sentence-transformers 3.0 — embeddings
- tiktoken 0.7.0 — token counting for chunking
- pypdf 4.2.0 — PDF parsing
- python-docx 1.1.0 — DOCX parsing

**Auth:**
- python-jose 3.3.0 — JWT tokens
- passlib 1.7.4 — password hashing
- bcrypt — bcrypt algorithm

**Testing:**
- pytest 8.2.0
- pytest-asyncio 0.23.0

### Code Style

```python
# Type hints mandatory on all functions
async def get_user_by_email(email: str) -> User | None:
    """Retrieve user by email address."""
    return await db.query(User).filter(User.email == email).first()

# Async/await throughout
async def process_document(doc_id: UUID) -> None:
    """Process document asynchronously."""
    doc = await get_document(doc_id)
    # ...

# Pydantic v2 for validation
from pydantic import BaseModel, Field

class CreateUserRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8)
    full_name: str | None = None

# No print statements; use logging
from loguru import logger

logger.info("User {email} registered", email=user.email)
```

### Module Structure

Each feature module follows:

```
module/
├── __init__.py
├── models.py       # SQLAlchemy models
├── schemas.py      # Pydantic request/response schemas
├── service.py      # Business logic (max 200 lines, consider splitting)
├── router.py       # FastAPI routes
└── (optional) utils.py  # Module-specific utilities
```

### Error Handling

```python
from fastapi import HTTPException, status

# Validate input
if not email:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Email is required"
    )

# Handle exceptions
try:
    await process_document()
except ValueError as e:
    logger.error("Processing failed: {error}", error=str(e))
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Document processing failed"
    )
```

### Database

- **Async SQLAlchemy 2.0 style** — `async_session()`, `AsyncSession`
- **UUID primary keys** — all models use UUID
- **Timestamps** — `created_at`, `updated_at` on all models
- **Foreign keys with CASCADE** — `ForeignKey(..., ondelete="CASCADE")`
- **Migrations** — Alembic, semantic versioning (001_initial_schema.py, etc.)

```python
from src.db.base import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

class User(BaseModel):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
```

### Testing

- **Framework** — pytest + pytest-asyncio
- **Async tests** — use `async def test_()` with `@pytest.mark.asyncio`
- **Fixtures** — use conftest.py for shared fixtures
- **Mocking** — minimize; prefer integration tests over unit tests
- **Coverage target** — ≥80% for business logic

```python
import pytest

@pytest.mark.asyncio
async def test_get_user_by_email():
    user = await user_service.create_user(
        email="test@example.com",
        password="securepass123",
        full_name="Test User"
    )
    retrieved = await user_service.get_user_by_email("test@example.com")
    assert retrieved.id == user.id
```

## Frontend (React 19 + TypeScript 5)

### Dependencies

**Core:**
- React 19.2.4 — UI framework
- TypeScript 5.9.3 — type safety
- Vite 5.4.21 — build tool
- React Router 7.13 — routing
- Tailwind CSS 4.2.2 — styling

**HTTP:**
- axios 1.14.0 — API client

**UI:**
- lucide-react — icons
- classname utilities (custom via Tailwind)

### Code Style

```typescript
// Strict mode always
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true
  }
}

// Type all function parameters and returns
function getUser(userId: string): Promise<User> {
  // ...
}

// Use interfaces, not type aliases, for complex objects
interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// Functional components with hooks
function ChatPage(): React.ReactElement {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const { user } = useAuth();
  
  return <div>{/* content */}</div>;
}
```

### Component Organization

```
components/
├── layout.tsx                 # Main layout wrapper
├── protected-route.tsx        # Auth guard
├── chat/
│   ├── chat-input.tsx        # Controlled form input
│   ├── chat-message.tsx      # Message bubble display
│   └── source-card.tsx       # Citation card
└── documents/
    ├── upload-zone.tsx       # Drag-drop upload
    ├── document-list.tsx     # Table view
    └── document-status-badge.tsx  # Status indicator
```

### State Management

- **Auth state** — React Context (`contexts/auth-context.tsx`)
- **Component state** — useState for local state
- **HTTP data** — fetch in useEffect, cache via API layer
- **No Redux** — too much overhead at this scale

```typescript
// Auth context
const AuthContext = createContext<AuthContextType | null>(null);

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
```

### API Layer

- **Centralized client** — `api/client.ts` with axios instance
- **Separate API modules** — `api/auth-api.ts`, `api/documents-api.ts`, etc.
- **Request/response types** — defined in `types/index.ts`
- **Error handling** — interceptors for 401 (redirect to login)

```typescript
// api/client.ts
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000'
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// api/auth-api.ts
export async function login(email: string, password: string): Promise<TokenResponse> {
  const response = await client.post<TokenResponse>('/auth/login', {
    email,
    password
  });
  return response.data;
}
```

### Styling

- **Tailwind CSS only** — no CSS modules or styled-components
- **Utility-first** — compose styles from Tailwind classes
- **Custom theme** — configured in `tailwind.config.js`
- **Responsive** — mobile-first with `sm:`, `md:`, `lg:` breakpoints
- **Dark mode** — supported via Tailwind, not implemented in v0.1.0

```tsx
export function ChatMessage({ message }: Props): React.ReactElement {
  return (
    <div className={`flex gap-4 p-4 rounded-lg ${
      message.role === 'user'
        ? 'bg-blue-100 ml-auto max-w-xs'
        : 'bg-gray-100 max-w-2xl'
    }`}>
      {message.content}
    </div>
  );
}
```

### Error Handling & Loading States

```typescript
function DocumentsList(): React.ReactElement {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listDocuments()
      .then(setDocuments)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error} />;
  if (!documents.length) return <EmptyState />;
  
  return <DocumentTable documents={documents} />;
}
```

## Git Conventions

### Commit Messages

Use Conventional Commits format:

```
type(scope): subject

- feat: new feature
- fix: bug fix
- docs: documentation changes
- refactor: code refactoring
- test: test additions/changes
- chore: dependencies, build, CI/CD

Examples:
feat(auth): add JWT token refresh endpoint
fix(rag): handle empty query strings gracefully
docs: update deployment guide for production
test(documents): add parser tests for DOCX files
```

### Branch Naming

```
feature/user-authentication
bugfix/rag-streaming-timeout
docs/deployment-guide
refactor/chunk-splitting-algorithm
```

### Commit Best Practices

- Keep commits focused on a single concern
- Don't commit `.env` files or secrets
- Don't commit `node_modules/` or `.venv/`
- Write descriptive commit messages
- Prefer atomic commits (can revert without breaking)

## Testing Strategy

### Backend

- **Unit tests** — business logic, validators, utilities
- **Integration tests** — database queries, API endpoints
- **Currently minimal** — `test_health.py` only; target ≥80% coverage in Phase 2

```bash
# Run all tests
cd backend && poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html
```

### Frontend

- **No tests in v0.1.0** — target Phase 2
- **Strategy (planned)** — React Testing Library + Vitest
- **Focus** — API integration, error states, auth flows

## Security Standards

### Passwords
- Minimum 8 characters
- Hashed with bcrypt (cost=12, library: passlib)
- Never logged or echoed

### JWT Tokens
- Algorithm: HS256
- Expiry: 24 hours (configurable via `ACCESS_TOKEN_EXPIRE_HOURS`)
- Stored in localStorage (frontend) — note: vulnerable to XSS; consider httpOnly cookies in Phase 2
- Query parameter for SSE streaming (since EventSource doesn't support custom headers)

### Database
- No credentials in code; use `.env` (not committed)
- User isolation enforced in retriever (`filter(Document.user_id == current_user.id)`)
- HTTPS in production (reverse proxy + TLS termination)

### File Uploads
- Extension whitelist: pdf, docx, txt, md
- Size limit: 50MB
- Saved to `./uploads/` with UUID prefix
- MIME type validation (not relying on extension alone)

## Linting & Formatting

### Backend
```bash
# Ruff (linter + formatter)
poetry run ruff check src/  # check
poetry run ruff format src/  # auto-format
```

### Frontend
```bash
# ESLint
npm run lint

# TypeScript
npm run type-check
```

## Environment Variables

Never commit `.env` files. Use `.env.example` as template. See [Deployment Guide](./deployment-guide.md) for full reference.
