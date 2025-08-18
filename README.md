# Zib RSS Reader

> An opinionated RSS reader inspired by Austrian news culture ("Zeit im Bild")

## 🌟 What is Zib?

Zib is a self-hosted RSS reader designed for power users who want advanced filtering capabilities and complete control over their news consumption. Unlike cloud-based RSS services, Zib runs on your own server and keeps your reading habits private.

[![image.png](https://i.postimg.cc/HxGr6Q54/image.png)](https://postimg.cc/VSRs60Kd)

### Key Features

- **🔒 Self-Hosted & Private** - Your data stays on your server
- **📱 Mobile-First Design** - Optimized for reading on any device
- **🌙 Dark Mode Only** - Easy on the eyes, opinionated design
- **⚡ Advanced Filtering** - Powerful content filtering with Boolean logic
- **🔄 Auto-Refresh** - Automatic feed updates every 5+ minutes
- **⭐ Smart Organization** - Categories, starring, and read status tracking
- **🎯 Webpage Redirect** - Open short articles directly in browser
- **📊 Unread Counts** - Real-time sidebar counters and browser title
- **📤 OPML Import/Export** - Easy migration from other RSS readers
- **🕐 Relative Timestamps** - See how old articles are at a glance

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose installed on your system
- 2GB free disk space
- Internet connection for RSS feeds

### Installation

1. **Download Zib**
   ```bash
   git clone https://github.com/faulander/zib.git
   cd zib
   ```

2. **Start Zib**
   ```bash
   docker-compose up -d
   ```

3. **Access Zib**
   - Open your browser to **http://localhost:3000**
   - The application will be ready in 1-2 minutes

That's it! Zib is now running on your machine.

## 📖 How to Use Zib

### Adding Feeds

1. **Click the Settings button** in the sidebar
2. **Go to "Feed Management"**
3. **Add categories first** (e.g., "News", "Tech", "Sports")
4. **Add RSS feeds** to your categories
5. **Or import an OPML file** from your previous RSS reader

### Reading Articles

- **Browse by category** - Click categories in the sidebar
- **Use filter buttons** - All, Unread, Starred at the top
- **Click articles** to read in modal, or open webpage for short articles
- **Star important articles** - Click the star icon
- **Mark as read** - Automatically when scrolling, or click manually

### Advanced Filtering

Create powerful filters in Settings > Filters:

- **Simple filters**: `React` (find articles mentioning React)
- **Phrase filters**: `"React Native"` (exact phrase)
- **Boolean logic**: `React OR Vue OR Angular` (multiple frameworks)
- **Complex filters**: `"React Native" OR RN AND mobile` (advanced queries)
- **Exclusion filters**: Set filter type to "does not contain"

### Auto-Refresh Settings

Configure automatic feed updates in Settings > General:

- **Enable auto-refresh** - Check the checkbox
- **Set interval** - 5 minutes minimum, 1440 maximum (24 hours)
- **Backend refreshes** feeds every N minutes
- **Frontend syncs** 1 minute after backend

### Customization

**General Settings:**
- **Default view** - Choose All/Unread/Starred as startup view
- **Show timestamps** - Toggle relative time display (20m, 3h20m, etc.)
- **Webpage redirect** - Open short articles directly in browser tabs
- **Unread count in title** - Show count in browser tab title

**Article Display:**
- **Short article threshold** - Set character limit for webpage redirect
- **Auto-refresh interval** - Customize how often feeds update

## 🛠️ Docker Commands

### Basic Operations

```bash
# Start Zib
docker-compose up -d

# View logs
docker-compose logs -f

# Stop Zib
docker-compose down

# Restart after changes
docker-compose restart

# Update to latest version
git pull
docker-compose up -d --build
```

### Data Management

```bash
# Backup your data
docker run --rm -v zib_zib_data:/data -v $(pwd):/backup alpine tar czf /backup/zib-backup.tar.gz -C /data .

# Restore from backup
docker run --rm -v zib_zib_data:/data -v $(pwd):/backup alpine tar xzf /backup/zib-backup.tar.gz -C /data

# Reset all data (WARNING: Deletes everything)
docker-compose down -v
docker-compose up -d
```

### Troubleshooting

```bash
# Check service status
docker-compose ps

# View detailed logs
docker-compose logs backend
docker-compose logs frontend

# Access backend container
docker-compose exec backend bash

# Check database
docker-compose exec backend uv run python -c "from app.models.article import User; print(f'Users: {User.select().count()}')"
```

## 🔧 Configuration

### Port Changes

Edit `docker-compose.yml` to change ports:

```yaml
services:
  frontend:
    ports:
      - "3001:3000"  # Use port 3001 instead of 3000
  backend:
    ports:
      - "8001:8000"  # Use port 8001 instead of 8000
```

### Environment Variables

**Backend:**
- `DATABASE_URL` - SQLite database path
- `AUTO_REFRESH_INTERVAL` - Default refresh interval
- `CORS_ORIGINS` - Allowed frontend origins

**Frontend:**
- `PUBLIC_API_BASE_URL` - Backend API URL
- `ORIGIN` - Frontend origin URL

## 📊 System Requirements

- **CPU**: 1 core minimum, 2+ cores recommended
- **RAM**: 512MB minimum, 1GB+ recommended
- **Storage**: 2GB minimum, 10GB+ for large feed collections
- **Network**: Internet connection for RSS feeds

## 🔄 Updates

Zib is actively developed. To update:

```bash
git pull
docker-compose up -d --build
```

Your data is preserved in Docker volumes during updates.

## 🐛 Getting Help

1. **Check logs**: `docker-compose logs -f`
2. **Restart services**: `docker-compose restart`
3. **Reset if needed**: `docker-compose down -v && docker-compose up -d`
4. **Open an issue** on GitHub with logs and error details

## 📜 License

MIT License - Use, modify, and distribute freely.

---

**Zib RSS Reader** - Take control of your news consumption with powerful filtering and complete privacy.
