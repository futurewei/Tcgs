# TCGS Development Todos

## Completed
- [x] Create project structure (Vue 3 + Vite + Tailwind)
- [x] Set up TypeScript types for all entities
- [x] Create API client with Axios
- [x] Create Pinia stores for state management
- [x] Create Vue Router configuration
- [x] Create main layout with TopBar and SideNav
- [x] Create Dashboard view with 12-column grid layout
- [x] Create TopicRow component with Stage Timeline
- [x] Create SlotChip component (status indicator + name)
- [x] Create Topics list and detail views
- [x] Create Capacity management view
- [x] Create Stage Templates management view with drag-drop
- [x] Create Wiki views (directions, pages, edit with Markdown)
- [x] Create Insights/History view with KPI, trends, load analysis
- [x] Create Admin views (Users, Audit Logs)
- [x] Create FastAPI backend with SQLAlchemy models
- [x] Create API routes for all entities
- [x] Create authentication with JWT
- [x] Create audit logging service
- [x] Create docker-compose configuration
- [x] Create README with setup instructions
- [x] Add demo mode with mock data for frontend testing

## System Features Implemented
- Dashboard with Topic Pools (Uncertainty/Evolution) and Capacity overview
- Stage Timeline from dynamic StageTemplates (not fixed DEF/POC/CLOSE)
- SlotChip with status indicator (available/partial/occupied)
- Topic detail with stage-based content, artifacts, reviews
- Closure only available on terminal stages
- DRI change restricted (EXTERNAL cannot be DRI)
- Force binding logged to audit trail
- Wiki with revision history (append-only)
- Insights with KPI, throughput trends, person load, external collab

## Architecture Notes
- Frontend: Vue 3 + Vite + TypeScript + Tailwind + Element Plus
- Backend: FastAPI + SQLAlchemy + PostgreSQL + JWT
- Storage: MinIO for attachments
- Deployment: docker-compose with postgres, minio, backend services
