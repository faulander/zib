# Zib RSS Reader - Docker Setup

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd zib
   ```

2. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Services

### Backend
- **Port**: 8000
- **Database**: SQLite (persisted in Docker volume)
- **Health Check**: `/health` endpoint
- **Auto-refresh**: Enabled for RSS feeds

### Frontend
- **Port**: 3000
- **Framework**: SvelteKit
- **Build**: Production optimized
- **API Connection**: Connects to backend on port 8000

## Docker Commands

### Start services
```bash
docker-compose up -d
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop services
```bash
docker-compose down
```

### Rebuild after code changes
```bash
docker-compose up -d --build
```

### Reset database (remove volume)
```bash
docker-compose down -v
docker-compose up -d
```

## Environment Variables

### Backend
- `DATABASE_URL`: SQLite database path
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Debug mode (default: false)
- `CORS_ORIGINS`: Allowed CORS origins

### Frontend
- `NODE_ENV`: Node environment (default: production)
- `ORIGIN`: Application origin URL
- `PUBLIC_API_BASE_URL`: Backend API URL

## Data Persistence

The SQLite database is stored in a Docker volume named `zib_data`. This ensures your feeds, articles, and settings persist across container restarts.

## Health Checks

Both services include health checks:
- **Backend**: Checks `/health` endpoint
- **Frontend**: Checks root URL availability

## Development

For development with hot reloading, use the local development setup instead of Docker:

```bash
# Backend
cd backend
uv run python -m app.main

# Frontend
cd frontend
npm run dev
```

## Troubleshooting

### Port conflicts
If ports 3000 or 8000 are in use, modify the docker-compose.yml file:
```yaml
ports:
  - "3001:3000"  # Use port 3001 instead
```

### Database issues
Reset the database volume:
```bash
docker-compose down -v
docker volume rm zib_zib_data
docker-compose up -d
```

### Check service status
```bash
docker-compose ps
```

### Access container shell
```bash
docker-compose exec backend bash
docker-compose exec frontend sh
```