# Forex Calendar Application - Setup Guide

This guide will help you set up and run the Forex Calendar application with seamless backend and frontend connectivity.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Modern web browser (Chrome, Firefox, Safari, Edge)

## Installation

### 1. Install Python Dependencies

Navigate to the project directory and install the required Python packages:

```bash
cd forex-calendar-repo
pip install -r requirements.txt
```

### 2. Verify Installation

The application requires the following key dependencies:
- FastAPI (Web framework)
- Uvicorn (ASGI server)
- Redis (Database - cloud-hosted)
- Botasaurus (Web scraping)
- Sentence Transformers (Text paraphrasing)

## Running the Application

### Option 1: Using the Startup Script (Recommended)

```bash
python start_backend.py
```

This script will:
- Check if all dependencies are installed
- Find an available port (8000-8010)
- Start the backend server
- Display connection information

### Option 2: Direct Backend Execution

```bash
python backend.py
```

### 3. Access the Frontend

Once the backend is running, open your web browser and navigate to:

```
http://localhost:8000/frontend/index.html
```

Or simply open the `frontend/index.html` file in your browser.

## Features

### Backend Features
- **FastAPI REST API** with automatic documentation
- **Redis Database** for caching scraped data
- **Web Scraping** of Forex Factory economic calendar
- **Text Paraphrasing** for enhanced readability
- **CORS Support** for frontend connectivity
- **Health Monitoring** and database statistics

### Frontend Features
- **Modern UI** with responsive design
- **Real-time Data Loading** from backend
- **Search and Filter** functionality
- **Export to CSV** capability
- **Database Management** tools
- **Connection Status** indicator

## API Endpoints

### Core Endpoints
- `GET /` - API information and status
- `GET /health` - Health check and Redis status
- `GET /events` - Retrieve forex events (paraphrased by default)
- `GET /events/original` - Retrieve original forex events
- `DELETE /database/delete` - Delete database records
- `GET /database/info` - Database statistics

### Query Parameters
- `start` - Start date (YYYY-MM-DD)
- `end` - End date (YYYY-MM-DD)
- `original` - Return original data instead of paraphrased (true/false)

## Usage Examples

### Load Events for Today
1. Set start and end dates to today
2. Click "Load Events"
3. Choose between paraphrased or original data using the toggle

### Search and Filter
- Use the search box to find events by currency or keyword
- Use the currency dropdown to filter by specific currencies
- Results update in real-time

### Export Data
- Load events first
- Apply any desired filters
- Click "Export CSV" to download the data

### Database Management
- View database statistics
- Delete records for specific date ranges
- Monitor Redis connection status

## Troubleshooting

### Backend Connection Issues

1. **Port Already in Use**
   - The application automatically finds an available port
   - Check the console output for the correct port number
   - Update frontend URL if needed

2. **Redis Connection Error**
   - The application uses a cloud-hosted Redis instance
   - Check internet connectivity
   - Verify Redis credentials in backend.py

3. **Dependencies Missing**
   ```bash
   pip install -r requirements.txt
   ```

### Frontend Issues

1. **CORS Errors**
   - Backend includes CORS middleware
   - Ensure you're accessing via HTTP, not file:// protocol
   - Use a local web server if needed

2. **Port Detection**
   - Frontend automatically detects backend port
   - Check browser console for connection status
   - Use the test page: `frontend/test.html`

### Testing Connection

Use the test page to verify connectivity:

```
http://localhost:8000/frontend/test.html
```

This page will:
- Detect the backend port automatically
- Test all API endpoints
- Verify CORS configuration
- Display detailed error messages

## Development

### Backend Development
- Edit `backend.py` for API changes
- Check logs in `backend.log`
- Use FastAPI docs at `http://localhost:8000/docs`

### Frontend Development
- Edit `frontend/app.js` for JavaScript changes
- Edit `frontend/style.css` for styling
- Edit `frontend/index.html` for HTML structure

### Database
- Redis database is cloud-hosted
- Data is automatically cached and retrieved
- Original and paraphrased data stored separately

## Security Notes

- CORS is configured for development (allows all origins)
- Redis credentials are included in the code (for demo purposes)
- In production, use environment variables for sensitive data

## Performance

- Database caching reduces scraping time
- Paraphrased data is pre-processed and cached
- Frontend includes loading states and error handling
- Automatic retry logic for failed requests

## Support

For issues or questions:
1. Check the browser console for error messages
2. Review the backend logs in `backend.log`
3. Use the test page to diagnose connection issues
4. Verify all dependencies are installed correctly



