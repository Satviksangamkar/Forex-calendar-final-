# Forex Economic Calendar

A comprehensive Forex Factory economic calendar scraper with a modern web frontend and FastAPI backend. The system scrapes economic events from Forex Factory, stores them in Redis, and provides both original and paraphrased data through a RESTful API.

## Features

- **Real-time Scraping**: Scrapes economic events from Forex Factory using Botasaurus
- **Redis Caching**: Efficient database storage with Redis for fast data retrieval
- **Paraphrasing Support**: Provides both original and paraphrased event data
- **Modern Frontend**: Responsive web interface with search, filtering, and export capabilities
- **RESTful API**: FastAPI backend with comprehensive endpoints
- **Database Management**: Built-in tools for managing cached data

## Project Structure

```
forex-calendar/
├── backend.py              # FastAPI backend server
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── frontend/
    ├── index.html         # Main HTML file
    ├── app.js            # JavaScript application logic
    ├── style.css         # CSS styling
    └── test.html         # Test page
```

## Backend (FastAPI)

The backend provides a comprehensive API for scraping and retrieving forex economic events.

### Key Features

- **Dual Database Storage**: Stores both original and paraphrased data separately
- **Intelligent Caching**: Only scrapes missing dates, uses cached data when available
- **Paraphrasing Engine**: Uses sentence-transformers for data enhancement
- **Robust Error Handling**: Comprehensive error handling and retry logic
- **Health Monitoring**: Built-in health checks and database statistics

### API Endpoints

- `GET /` - API information and status
- `GET /health` - Health check endpoint
- `GET /events` - Retrieve forex events (paraphrased by default)
- `GET /events/original` - Retrieve original forex events
- `DELETE /database/delete` - Delete database records for date range
- `GET /database/info` - Database statistics

### Configuration

The backend uses Redis for data storage with the following configuration:
- **Host**: redis-13632.c280.us-central1-2.gce.redns.redis-cloud.com
- **Port**: 13632
- **Username**: default
- **Password**: wkSlVhquYcUAl6tMidvYJVeoD2WtBzuL

## Frontend

A modern, responsive web interface built with vanilla JavaScript, HTML, and CSS.

### Features

- **Real-time Data Loading**: Load economic events for any date range
- **Search and Filtering**: Search by keyword and filter by currency
- **Data Toggle**: Switch between original and paraphrased data
- **Export Functionality**: Export events to CSV format
- **Database Management**: View statistics and delete data ranges
- **Responsive Design**: Works on desktop and mobile devices

### Key Components

- **Date Range Selection**: Choose start and end dates for data retrieval
- **Data Type Toggle**: Switch between original and paraphrased data
- **Search Interface**: Real-time search through events
- **Currency Filter**: Filter events by specific currencies
- **Event Details Modal**: View detailed information for each event
- **Database Statistics**: Monitor database usage and performance

## Installation and Setup

### Prerequisites

- Python 3.8+
- Node.js (for development server)
- Redis database access

### Backend Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Start the backend server:
```bash
python backend.py
```

The server will start on `http://localhost:8000` (or the next available port).

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Open `index.html` in a web browser or serve it using a local server:
```bash
# Using Python
python -m http.server 8080

# Using Node.js
npx serve .
```

3. Access the application at `http://localhost:8080`

## Usage

### Loading Events

1. Select a start and end date in the header
2. Choose between original or paraphrased data using the toggle
3. Click "Load Events" to retrieve data
4. Use search and currency filters to narrow down results

### Database Management

1. View database statistics in the "Database Management" section
2. Use "Delete Range" to remove cached data for specific dates
3. Monitor connection status with the health indicator

### Exporting Data

1. Load events for your desired date range
2. Apply any filters as needed
3. Click "Export CSV" to download the data

## API Examples

### Get Events (Paraphrased)
```bash
curl "http://localhost:8000/events?start=2025-08-16&end=2025-08-17"
```

### Get Original Events
```bash
curl "http://localhost:8000/events?start=2025-08-16&end=2025-08-17&original=true"
```

### Health Check
```bash
curl "http://localhost:8000/health"
```

### Database Statistics
```bash
curl "http://localhost:8000/database/info"
```

## Technical Details

### Backend Technologies

- **FastAPI**: Modern Python web framework
- **Redis**: In-memory data store for caching
- **Botasaurus**: Web scraping automation
- **Sentence Transformers**: Text paraphrasing and enhancement
- **Pydantic**: Data validation and serialization

### Frontend Technologies

- **Vanilla JavaScript**: No framework dependencies
- **CSS Grid/Flexbox**: Modern layout techniques
- **Responsive Design**: Mobile-first approach
- **Local Storage**: Client-side caching

### Data Flow

1. **Request**: Frontend requests events for date range
2. **Cache Check**: Backend checks Redis for existing data
3. **Scraping**: If needed, scrapes missing dates from Forex Factory
4. **Processing**: Applies paraphrasing if requested
5. **Storage**: Saves both original and paraphrased data to Redis
6. **Response**: Returns formatted data to frontend

## Error Handling

The system includes comprehensive error handling:

- **Network Errors**: Automatic retry with exponential backoff
- **Scraping Failures**: Graceful degradation with partial data
- **Database Errors**: Connection monitoring and recovery
- **User Input Validation**: Client and server-side validation

## Performance Optimizations

- **Intelligent Caching**: Only scrapes missing dates
- **Database Optimization**: Efficient Redis key structure
- **Frontend Caching**: Client-side data caching
- **Lazy Loading**: Load data only when needed
- **Compression**: Optimized data transfer

## Security Considerations

- **Input Validation**: Comprehensive validation of all inputs
- **Rate Limiting**: Built-in protection against abuse
- **Error Sanitization**: Safe error message handling
- **CORS Configuration**: Configurable cross-origin settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the GitHub repository.
