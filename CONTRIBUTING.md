# Contributing to Zib RSS Reader

> Developer and contributor guide for Zib RSS Reader

## 🏗️ Architecture Overview

Zib is a modern RSS reader built with a clear separation between backend and frontend:

- **Backend**: Python FastAPI with SQLite database using Peewee ORM
- **Frontend**: SvelteKit with Svelte 5 runes syntax and TailwindCSS
- **Deployment**: Docker containers with health checks and volume persistence

### Tech Stack Details

**Backend:**
- FastAPI 0.104+ with async support
- Peewee ORM for database operations
- SQLite for data persistence
- uvicorn ASGI server
- uv for Python package management
- feedparser for RSS/Atom parsing
- BeautifulSoup4 for HTML sanitization

**Frontend:**
- SvelteKit with adapter-node
- Svelte 5 with runes syntax ($state, $derived, $effect)
- TailwindCSS 4.0+ for styling
- Lucide icons for UI elements
- Vite for build tooling

## 🚀 Development Setup

### Prerequisites

- Python 3.12+
- Node.js 22 LTS
- Docker and Docker Compose (for production testing)
- Git

### Backend Development

1. **Clone and setup**
   ```bash
   git clone https://www.github.com/faulander/zib.git
   cd zib/backend
   ```

2. **Install uv package manager**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install dependencies**
   ```bash
   uv sync
   ```

4. **Initialize database**
   ```bash
   uv run python init_db.py
   uv run python run_migrations.py
   ```

5. **Start development server**
   ```bash
   uv run python -m app.main
   ```

   Backend runs on http://localhost:8000

### Frontend Development

1. **Setup frontend**
   ```bash
   cd zib/frontend
   npm install
   ```

2. **Start development server**
   ```bash
   npm run dev
   ```

   Frontend runs on http://localhost:5173

### Testing

**Backend tests:**
```bash
cd backend
uv run python -m pytest tests/ -v
uv run python -m pytest tests/unit/test_models.py -v
```

**Frontend tests:**
```bash
cd frontend
npm run test
npm run test:unit
```

## 📁 Project Structure

```
zib/
├── backend/
│   ├── app/
│   │   ├── core/           # Database and config
│   │   ├── models/         # Data models
│   │   ├── routes/         # API endpoints
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI app
│   ├── migrations/         # Database migrations
│   ├── tests/             # Backend tests
│   ├── init_db.py         # Database initialization
│   ├── run_migrations.py  # Migration runner
│   └── start.sh           # Docker startup script
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── components/ # Svelte components
│   │   │   ├── stores/     # Svelte stores
│   │   │   └── services/   # API services
│   │   └── routes/         # SvelteKit routes
│   ├── static/            # Static assets
│   └── tests/             # Frontend tests
├── docker-compose.yml     # Production deployment
└── README.md             # End-user documentation
```

## 🔧 Development Workflow

### Making Changes

1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Backend changes**
   - Modify code in `backend/app/`
   - Add tests in `backend/tests/`
   - Run tests: `uv run python -m pytest`

3. **Frontend changes**
   - Modify components in `frontend/src/`
   - Follow Svelte 5 runes syntax
   - Test in browser at http://localhost:5173

4. **Database changes**
   - Create new migration in `backend/migrations/`
   - Follow naming: `XXX_description.py`
   - Test migration: `uv run python run_migrations.py`

### Code Standards

**Python (Backend):**
- Follow PEP 8 with line length 88 (Black compatible)
- Use type hints for all functions
- Prefer async/await for I/O operations
- Use Pydantic for data validation

**JavaScript (Frontend):**
- Use Svelte 5 runes syntax ($state, $derived, $effect)
- Prefer composition API over options
- Use TypeScript where beneficial
- Follow TailwindCSS utility-first approach

### API Design

**REST API patterns:**
```python
# GET /api/articles - List articles with filtering
# GET /api/articles/{id} - Get single article
# POST /api/articles - Create article
# PUT /api/articles/{id} - Update article
# DELETE /api/articles/{id} - Delete article
```

**Response format:**
```json
{
  "success": true,
  "data": {...},
  "message": "Optional message"
}
```

## 🗄️ Database Schema

### Core Models

**User**: Single-user system with settings
- `id, username, email, password_hash`
- `default_view, auto_refresh_interval_minutes`
- `show_timestamps_in_list, redirect_to_webpage`

**Category**: Feed organization
- `id, name, color, created_at`

**Feed**: RSS/Atom feed sources
- `id, title, url, description, category_id`
- `last_fetched, is_active, error_count`

**Article**: Individual news articles
- `id, title, content, summary, author`
- `published_at, guid, feed_id`

**ReadStatus**: Per-user article status
- `user_id, article_id, is_read, is_starred`
- `read_at, starred_at`

### Migrations

Create new migrations in `backend/migrations/`:

```python
# migrations/XXX_add_new_feature.py
from app.core.database import db

def up():
    """Apply migration"""
    db.execute_sql('''
        ALTER TABLE users ADD COLUMN new_setting BOOLEAN DEFAULT FALSE
    ''')

def down():
    """Rollback migration"""
    db.execute_sql('''
        ALTER TABLE users DROP COLUMN new_setting
    ''')
```

## 🎨 Frontend Architecture

### Svelte 5 Runes

Use modern Svelte 5 syntax:

```javascript
// Reactive state
let count = $state(0);

// Derived values
let doubled = $derived(count * 2);

// Complex derivations
let complexValue = $derived.by(() => {
    return someExpensiveCalculation(count);
});

// Side effects
$effect(() => {
    console.log('Count changed:', count);
});
```

### Component Structure

```svelte
<script>
    // Props
    let { articles = [], selectedFeed } = $props();
    
    // Local state
    let isLoading = $state(false);
    
    // Derived state
    let filteredArticles = $derived(
        articles.filter(a => !selectedFeed || a.feed_id === selectedFeed.id)
    );
    
    // Effects
    $effect(() => {
        if (selectedFeed) {
            loadArticles();
        }
    });
</script>
```

### Store Pattern

```javascript
// stores/api.js
import { writable } from 'svelte/store';

export const articles = writable([]);
export const selectedFeed = writable(null);

export const apiActions = {
    async loadArticles() {
        const response = await fetch('/api/articles');
        const data = await response.json();
        articles.set(data.articles);
    }
};
```

## 🐳 Docker Development

### Local Testing with Docker

```bash
# Build and start services
docker-compose up --build

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop services
docker-compose down
```

### Multi-stage Builds

Both Dockerfiles use multi-stage builds for optimization:

**Backend**: Python base → uv install → copy code → health checks
**Frontend**: Node build → production build → runtime image

## 🧪 Testing Guidelines

### Backend Testing

```python
# tests/test_articles.py
import pytest
from app.models.article import Article, User
from app.services.article_service import ArticleService

def test_create_article():
    user = User.create(username='test', email='test@example.com')
    article = Article.create(
        title='Test Article',
        content='Test content',
        feed_id=1
    )
    assert article.title == 'Test Article'
```

### Frontend Testing

```javascript
// tests/components/ArticleList.test.js
import { render, screen } from '@testing-library/svelte';
import ArticleList from '$lib/components/ArticleList.svelte';

test('renders article list', () => {
    const articles = [
        { id: 1, title: 'Test Article', content: 'Content' }
    ];
    
    render(ArticleList, { articles });
    expect(screen.getByText('Test Article')).toBeInTheDocument();
});
```

## 🚀 Deployment

### Production Build

```bash
# Build optimized containers
docker-compose build

# Deploy with health checks
docker-compose up -d

# Monitor deployment
docker-compose ps
docker-compose logs -f
```

### Environment Variables

**Production overrides in docker-compose.override.yml:**
```yaml
version: '3.8'
services:
  backend:
    environment:
      - DEBUG=false
      - AUTO_REFRESH_INTERVAL=300
  frontend:
    environment:
      - NODE_ENV=production
```

## 🤝 Contributing

### Pull Request Process

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open pull request with:
   - Clear description of changes
   - Screenshots for UI changes
   - Test coverage for new features

### Code Review

We look for:
- **Functionality**: Does it work as intended?
- **Performance**: No unnecessary overhead
- **Security**: No exposed secrets or SQL injection
- **UX**: Consistent with existing interface
- **Tests**: Adequate coverage for new features

### Issue Templates

**Bug Report:**
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Logs and screenshots

**Feature Request:**
- Problem description
- Proposed solution
- Alternative solutions considered
- Additional context

## 🔍 Debugging

### Common Issues

**Backend not starting:**
```bash
# Check database
uv run python -c "from app.core.database import db; print(db.connect())"

# Check migrations
uv run python run_migrations.py

# Verbose logging
uv run python -m app.main --debug
```

**Frontend build errors:**
```bash
# Clear node modules
rm -rf node_modules package-lock.json
npm install

# Check SvelteKit config
npm run check
```

**Docker issues:**
```bash
# Rebuild containers
docker-compose down -v
docker-compose up --build

# Check health
docker-compose ps
docker-compose logs backend
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Svelte 5 Documentation](https://svelte.dev/docs/svelte/overview)
- [SvelteKit Documentation](https://kit.svelte.dev/docs)
- [TailwindCSS Documentation](https://tailwindcss.com/docs)
- [Peewee ORM Documentation](http://docs.peewee-orm.com/)
- [uv Package Manager](https://github.com/astral-sh/uv)

## 📄 License

MIT License - See LICENSE file for details.

---

**Ready to contribute?** Start by setting up the development environment and exploring the codebase. We welcome all contributions, from bug fixes to new features!