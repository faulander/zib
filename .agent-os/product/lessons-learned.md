# Lessons Learned

> Last Updated: 2025-08-16
> Version: 1.0.0

## Development Workflow

### Development Server
- **Never run the development server** - Dev server is already running in another terminal
- Always assume the dev environment is active and accessible
- Focus on code changes rather than server management

### Code Quality
- **Never mention AI involvement** in commits, comments, or documentation
- Write code and commit messages as if written by a human developer
- Focus on technical implementation details, not the development process

## Database Management

### SQLite Operations
- **Always check the SQLite database for structural questions**
- Use database inspection before making schema assumptions
- Verify existing tables, columns, and relationships before modifications
- Query the database directly to understand current data structure

### Migration System
- **NEVER manually create or delete database tables** - This breaks production deployments
- Always use the proper migration system (`uv run python -m app.core.migrations`) 
- The system must work automatically without user intervention in production
- Debug migration issues by fixing the migration files, not by manual table operations
- If tables are missing, the issue is in the migration system that needs to be fixed

## Frontend Development

### Svelte 5 Syntax
- **Always use Svelte 5 runes syntax** for reactive state management
- Use `$state()`, `$derived()`, `$effect()` instead of legacy reactive statements
- Prefer the new runes API over stores when possible

### Derived State
- **Use `derived.by` instead of `derived`** for derived state calculations
- `derived.by` is the preferred pattern for computed values
- This provides better performance and cleaner syntax

## Code Patterns

### State Management
- Use `$state()` for component-level reactive variables
- Use `$derived.by()` for computed values based on other state
- Use `$effect()` for side effects and cleanup

### Database Queries
- Always verify table structure before writing queries
- Check existing column names and types
- Use proper SQLite syntax and constraints