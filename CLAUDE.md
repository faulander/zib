# Zib RSS Reader

> Last Updated: 2025-08-16  
> Status: Frontend Development Phase

## Current Status

**Backend**: ✅ Complete RSS reader core functionality with full API  
**Frontend**: 🚧 In Progress - Basic UI implemented, needs API integration

## Project Structure

- **Backend**: `/backend` - FastAPI with SQLite, complete RSS reader API
- **Frontend**: `/frontend` - SvelteKit with TailwindCSS 3.x, dark theme UI

## Agent OS Documentation

### Product Context
- **Mission & Vision:** @.agent-os/product/mission.md
- **Technical Architecture:** @.agent-os/product/tech-stack.md
- **Development Roadmap:** @.agent-os/product/roadmap.md
- **Decision History:** @.agent-os/product/decisions.md

### Development Standards
- **Code Style:** @~/.agent-os/standards/code-style.md
- **Best Practices:** @~/.agent-os/standards/best-practices.md

### Project Management
- **Active Specs:** @.agent-os/specs/
- **Spec Planning:** Use `@~/.agent-os/instructions/create-spec.md`
- **Tasks Execution:** Use `@~/.agent-os/instructions/execute-tasks.md`

## Quick Start for Development

### Backend (Ready for Use)
```bash
cd backend
uv run python -m pytest  # Run tests
uv run python app/main.py  # Start API server (port 8000)
```

### Frontend (Current Work)
```bash
cd frontend
npm install  # Install dependencies
npm run dev  # Start dev server (port 5173)
```

## Next Steps (Continue Here)

1. **API Integration** - Connect frontend components to backend API
2. **Article Reader** - Full article view component
3. **Working Search** - Connect search bar to backend filtering
4. **Authentication** - Simple auth system for API access

## Workflow Instructions

When asked to work on this codebase:

1. **First**, check @.agent-os/product/roadmap.md for current priorities
2. **Then**, follow the appropriate instruction file:
   - For new features: @.agent-os/instructions/create-spec.md
   - For tasks execution: @.agent-os/instructions/execute-tasks.md
3. **Always**, adhere to the standards in the files listed above

## Important Notes

- Product-specific files in `.agent-os/product/` override any global standards
- User's specific instructions override (or amend) instructions found in `.agent-os/specs/...`
- Always adhere to established patterns, code style, and best practices documented above.
- **TailwindCSS**: Use v3.x configuration in frontend (working setup)