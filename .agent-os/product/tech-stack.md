# Technical Stack

> Last Updated: 2025-08-16
> Version: 1.0.0

## Backend

- **Application Framework:** Python FastAPI with uv package manager
- **Language:** Python 3.12 with Pydantic
- **Database System:** SQLite
- **ORM:** Peewee
- **API Architecture:** RESTful API (all logic on backend)

## Frontend

- **JavaScript Framework:** SvelteKit with Svelte 5 Runes Syntax
- **Build Tool:** Vite
- **Import Strategy:** Node.js modules
- **Package Manager:** npm
- **Node Version:** 22 LTS

## UI/Design

- **CSS Framework:** TailwindCSS 4.0+
- **UI Components:** Custom components (mobile-first)
- **Font Provider:** Google Fonts
- **Font Loading:** From Google
- **Icon Library:** Lucide Svelte components
- **Theme Support:** Dark/Light mode

## Infrastructure

- **Application Hosting:** Docker (self-hosted)
- **Database Hosting:** SQLite (local file)
- **Asset Hosting:** Static files served by FastAPI
- **Deployment Solution:** Docker Compose
- **CI/CD Platform:** GitHub Actions
- **CI/CD Trigger:** Push to main/staging branches
- **Tests:** Run before deployment
- **Production Environment:** main branch
- **Staging Environment:** staging branch

## Development

- **Code Repository:** GitHub
- **Version Control:** Git
- **Testing Framework:** pytest (backend), Vitest (frontend)
- **Code Quality:** Ruff (Python), ESLint (JavaScript)