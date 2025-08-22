# Forex Calendar System

A comprehensive Forex Factory calendar scraper with Redis caching and a modern web frontend.

## System Overview

This system consists of:
- **Backend API**: FastAPI server with Redis database caching
- **Frontend**: Modern web interface for viewing and managing forex events
- **Scraper**: Automated scraping of Forex Factory calendar data

## Quick Start

### Option 1: Using the Batch File (Recommended)
1. Double-click `start_servers.bat` to start both servers automatically
2. The frontend will open in your browser at http://localhost:8080

### Option 2: Manual Start

#### Start Backend Server
```bash
cd forex-calendar-repo
uvicorn test_backend:app --host 127.0.0.1 --port 8000 --reload
```

#### Start Frontend Server
```bash
cd forex-calendar-repo/frontend
python -m http.server 8080
```

## Access Points

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Features

### Frontend Features
- 📅 Date range selection for forex events
- 🔍 Search and filter by currency/keyword
- 📊 Impact-based color coding (High/Medium/Low)
- 📋 Export events to CSV
- 🗄️ Database management interface
- 📱 Responsive design for mobile/desktop

### Backend Features
- 🚀 FastAPI with automatic API documentation
- 💾 Redis database caching for performance
- 🔄 Database-aside pattern for optimal data retrieval
- 🌐 CORS enabled for frontend integration
- 📊 Health monitoring and statistics

### API Endpoints

#### GET /health
Health check endpoint to verify backend status.

#### GET /events?start=YYYY-MM-DD&end=YYYY-MM-DD
Retrieve forex events for a specific date range.

**Parameters:**
- `start`: Start date (YYYY-MM-DD format)
- `end`: End date (YYYY-MM-DD format)

**Response:**
```json
{
  "success": true,
  "data": [...],
  "total_events": 5,
  "date_range": {"start": "2025-08-16", "end": "2025-08-17"},
  "source": "database",
  "timestamp": "2025-01-27T10:30:00",
  "processing_time_ms": 150
}
```

#### GET /database/info
Get Redis database statistics and information.

#### DELETE /database/delete?start=YYYY-MM-DD&end=YYYY-MM-DD
Delete database records for a specific date range.

## Database Structure

The system uses Redis with the following key pattern:
- `forex:events:YYYY-MM-DD` - Events for a specific date

## Configuration

### Environment Variables
- `REDIS_HOST`: Redis server host (default: redis-13632.c280.us-central1-2.gce.redns.redis-cloud.com)
- `REDIS_PORT`: Redis server port (default: 13632)
- `REDIS_USERNAME`: Redis username (default: default)
- `REDIS_PASSWORD`: Redis password

## Troubleshooting

### Backend Issues
1. Check if Redis connection is working
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Check backend logs for error messages

### Frontend Issues
1. Ensure backend is running on port 8000
2. Check browser console for JavaScript errors
3. Verify CORS settings if accessing from different domain

### Port Conflicts
If ports 8000 or 8080 are in use:
- Backend: Change port in uvicorn command
- Frontend: Change port in python http.server command
- Update frontend `baseUrl` in `app.js` if backend port changes

## Development

### Adding New Features
1. Backend: Add new endpoints in `test_backend.py`
2. Frontend: Update `app.js` and `index.html` as needed
3. Test thoroughly before deployment

### Dependencies
- Python 3.8+
- FastAPI
- Redis
- Uvicorn
- Pydantic

## Support

For issues or questions:
1. Check the logs in the server windows
2. Verify network connectivity
3. Test API endpoints directly using curl or browser
