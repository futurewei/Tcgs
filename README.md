# TCGS - Topic & Capacity Governance System

A comprehensive internal web system for managing topics, capacity slots, wiki documentation, and governance workflows.

## Features

- **Topics Management**: Create and track topics with configurable stage templates
- **Capacity Slots**: Manage algorithm team and external collaborator capacity
- **Wiki**: Documentation with version control and revision history
- **Stage Templates**: Customizable workflow stages for different topic types
- **Insights & History**: KPI dashboard, throughput trends, and load analysis
- **Audit Logging**: Full audit trail for all changes
- **RBAC**: Role-based access control (Admin, Member, Reviewer, External)

## Tech Stack

### Frontend
- Vue.js 3 + TypeScript
- Vite
- Tailwind CSS
- Element Plus
- Pinia (State Management)
- Vue Router
- Axios
- md-editor-v3 (Markdown)

### Backend
- FastAPI (Python)
- SQLAlchemy ORM
- Alembic (Migrations)
- PostgreSQL
- JWT Authentication
- MinIO (File Storage)

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone and enter directory
cd tcgs

# Start all services
docker-compose up -d

# Wait for services to start, then access:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# MinIO Console: http://localhost:9001
```

### Option 2: Manual Setup

#### Prerequisites
- Node.js 18+ or Bun
- Python 3.11+
- PostgreSQL 15+
- MinIO (optional, for file storage)

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/tcgs"
export SECRET_KEY="your-secret-key-change-in-production"

# Create database
createdb tcgs

# Run seed script (creates initial data and admin user)
python seed.py

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
# Install dependencies
bun install

# Set API URL
export VITE_API_URL="http://localhost:8000/api"

# Start dev server
bun run dev
```

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@tcgs.local | admin123 |
| Member | member@tcgs.local | member123 |
| Reviewer | reviewer@tcgs.local | reviewer123 |
| External | external@tcgs.local | external123 |

## Governance Rules

### Enforced by Backend

1. **DRI Requirement**: Every topic must have exactly one DRI (Directly Responsible Individual)
2. **EXTERNAL Restriction**: EXTERNAL users can never be assigned as DRI
3. **Append-Only**: Reviews and Wiki revisions are append-only (cannot be deleted or modified)
4. **Audit Trail**: All sensitive changes are logged:
   - Result changes
   - DRI changes
   - Slot force assignments
5. **Admin-Only Operations**:
   - Configure capacity slots
   - Manage user roles
   - Force slot bindings beyond capacity

## API Documentation

After starting the backend, access the interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
tcgs/
├── src/                      # Frontend source
│   ├── api/                  # API client
│   ├── components/           # Vue components
│   ├── router/               # Vue Router config
│   ├── stores/               # Pinia stores
│   ├── types/                # TypeScript types
│   ├── views/                # Page views
│   └── main.ts               # Entry point
├── backend/                  # Backend source
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── main.py           # FastAPI app
│   ├── alembic/              # Database migrations
│   ├── requirements.txt
│   └── seed.py               # Initial data
├── docker-compose.yml
└── README.md
```

## Data Models

### Core Entities

- **User**: System users with roles (ADMIN, MEMBER, REVIEWER, EXTERNAL)
- **Topic**: Main entity for tracking work items
- **StageTemplate**: Configurable workflow templates
- **StageTemplateStage**: Individual stages within a template
- **TopicStageState**: Tracks topic progress through stages
- **Artifact**: Deliverables attached to stages
- **ReviewComment**: Append-only review comments
- **CapacitySlot**: Resource capacity (ALGO or EXTERNAL)
- **Binding**: Links topics to capacity slots
- **WikiDirection/Page/Revision**: Documentation with version control
- **AuditLog**: System audit trail

## Environment Variables

### Backend

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection URL | postgresql://postgres:postgres@localhost:5432/tcgs |
| SECRET_KEY | JWT signing key | (required) |
| MINIO_ENDPOINT | MinIO server address | localhost:9000 |
| MINIO_ACCESS_KEY | MinIO access key | minioadmin |
| MINIO_SECRET_KEY | MinIO secret key | minioadmin |
| MINIO_BUCKET | Storage bucket name | tcgs-attachments |

### Frontend

| Variable | Description | Default |
|----------|-------------|---------|
| VITE_API_URL | Backend API URL | http://localhost:8000/api |

## License

MIT License
