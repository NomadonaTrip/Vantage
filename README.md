# Vantage

[![CI](https://github.com/NomadonaTrip/Vantage/actions/workflows/ci.yml/badge.svg)](https://github.com/NomadonaTrip/Vantage/actions/workflows/ci.yml)
[![Security](https://github.com/NomadonaTrip/Vantage/actions/workflows/security.yml/badge.svg)](https://github.com/NomadonaTrip/Vantage/actions/workflows/security.yml)

**Intelligent Lead Generation Platform**

Vantage is an AI-powered lead generation platform that helps agencies find and qualify potential clients through intelligent search, scoring, and conversation.

## Features

- **AI-Powered Search**: Multi-source lead discovery across Upwork, Reddit, Apollo, and more
- **Smart Scoring**: ML-based lead quality scoring with intent signal detection
- **Conversational Interface**: Natural language interface for search configuration
- **Real-time Tracking**: Live lead status updates and conversion analytics
- **Voice Mode**: Optional voice interaction for hands-free operation

## Quick Start

```bash
# Clone the repository
git clone https://github.com/NomadonaTrip/Vantage.git
cd Vantage

# Install dependencies
pnpm install

# Start infrastructure (PostgreSQL, Redis)
docker-compose up -d

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start development servers
pnpm dev
```

## Prerequisites

- **Node.js** 20.x or higher
- **pnpm** 9.x or higher
- **Python** 3.11 or higher
- **Poetry** 1.7 or higher
- **Docker** and Docker Compose
- **Git**

### Installing Prerequisites

```bash
# Install Node.js (using nvm)
nvm install 20
nvm use 20

# Install pnpm
corepack enable
corepack prepare pnpm@9 --activate

# Install Python (using pyenv)
pyenv install 3.11
pyenv local 3.11

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

## Environment Setup

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure required services:**

   | Variable | Description | Required |
   |----------|-------------|----------|
   | `DATABASE_URL` | PostgreSQL connection string | Yes |
   | `REDIS_URL` | Redis connection string | Yes |
   | `SUPABASE_URL` | Supabase project URL | Yes |
   | `SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
   | `SENTRY_DSN` | Sentry error tracking DSN | Recommended |

3. **Start infrastructure:**
   ```bash
   docker-compose up -d
   ```

## Development Commands

### Monorepo Commands

```bash
# Install all dependencies
pnpm install

# Start all development servers
pnpm dev

# Build all packages
pnpm build

# Run all tests
pnpm test

# Run linting
pnpm lint

# Type checking
pnpm typecheck

# Clean all build artifacts
pnpm clean
```

### Docker Commands

```bash
# Start PostgreSQL and Redis only
docker-compose up -d

# Start full stack (with API and Web)
docker-compose --profile full up -d

# Start API only
docker-compose --profile api up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Remove volumes (clean slate)
docker-compose down -v
```

### Backend Commands (apps/api)

```bash
cd apps/api

# Install Python dependencies
poetry install

# Run API server
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
poetry run pytest

# Run linting
poetry run ruff check .

# Run type checking
poetry run mypy src/
```

### Frontend Commands (apps/web)

```bash
cd apps/web

# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for production
pnpm build

# Run tests
pnpm test

# Run accessibility tests
pnpm test:a11y
```

## Project Structure

```
vantage/
├── apps/
│   ├── api/                 # FastAPI backend
│   │   ├── src/
│   │   │   ├── api/         # Routes and middleware
│   │   │   ├── core/        # Core modules (Sentry, etc.)
│   │   │   ├── services/    # Business logic
│   │   │   └── utils/       # Utilities (logging, etc.)
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   └── web/                 # Next.js frontend
│       ├── app/             # App Router pages
│       ├── components/      # React components
│       ├── lib/             # Utilities and clients
│       ├── hooks/           # Custom React hooks
│       ├── stores/          # Zustand stores
│       ├── package.json
│       └── Dockerfile
│
├── packages/
│   └── shared/              # Shared types and utilities
│       └── src/types/
│
├── docs/                    # Documentation
│   ├── prd/                 # Product requirements
│   ├── architecture/        # Architecture docs
│   └── stories/             # User stories
│
├── .github/
│   └── workflows/           # CI/CD pipelines
│
├── docker-compose.yml       # Local development
├── turbo.json               # Turborepo configuration
├── pnpm-workspace.yaml      # pnpm workspace
└── package.json             # Root package
```

## Testing

### Running Tests

```bash
# Run all tests
pnpm test

# Run frontend tests only
cd apps/web && pnpm test

# Run backend tests only
cd apps/api && poetry run pytest

# Run with coverage
cd apps/api && poetry run pytest --cov=src
```

### Test Types

- **Unit Tests**: Component and function-level tests
- **Integration Tests**: API endpoint tests
- **Accessibility Tests**: WCAG compliance testing
- **E2E Tests**: End-to-end user flow tests (coming soon)

## Code Quality

The project enforces code quality through:

- **ESLint**: JavaScript/TypeScript linting
- **Ruff**: Python linting and formatting
- **MyPy**: Python type checking
- **Pre-commit hooks**: Automated checks before commit
- **CI Pipeline**: Automated testing on pull requests

## Architecture

For detailed architecture documentation, see:

- [Architecture Overview](docs/architecture/index.md)
- [Tech Stack](docs/architecture/tech-stack.md)
- [Database Schema](docs/architecture/database-schema.md)
- [API Design](docs/architecture/backend-architecture.md)
- [ADRs](docs/architecture/adr.md)

## Contributing

1. Create a feature branch from `master`
2. Make your changes
3. Ensure tests pass: `pnpm test`
4. Ensure linting passes: `pnpm lint`
5. Submit a pull request

## License

Proprietary - Orban Forest Inc.
