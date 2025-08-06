# Video Generator API

A FastAPI application that generates educational videos using Manim (Mathematical Animation Engine), Gemini AI, and Azure TTS.

## Features

- **AI-Powered Script Generation**: Uses Gemini to generate Manim scripts from text prompts
- **Video Processing**: Renders educational videos using Manim
- **RESTful API**: Clean REST endpoints for video management
- **Background Processing**: Async video generation with progress tracking
- **File Management**: Automatic cleanup and storage management
- **Health Monitoring**: Health checks and system status endpoints
- **Docker Support**: Easy deployment with Docker and Docker Compose

## Project Structure

```
manim_video_generator/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app setup
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py        # API endpoints
│   │   └── dependencies.py  # Dependency injection
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration settings
│   │   └── exceptions.py    # Custom exceptions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── script_generator.py  # AI script generation
│   │   ├── video_processor.py   # Manim video processing
│   │   └── storage.py           # Video storage management
│   └── models/
│       ├── __init__.py
│       └── video.py         # Pydantic models
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Installation

### Prerequisites

- Python 3.10+
- FFmpeg
- LaTeX (for mathematical expressions)
- Anthropic API key

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd manim_video_generator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install manim
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Anthropic API key
   ```

5. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Deployment

1. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

## API Endpoints

### Video Management

- `POST /api/v1/videos` - Create a new video generation request
- `GET /api/v1/videos/{video_id}/status` - Check video generation status
- `GET /api/v1/videos/{video_id}/download` - Download completed video
- `GET /api/v1/videos/{video_id}/script` - Get the generated Manim script
- `DELETE /api/v1/videos/{video_id}` - Delete video and files
- `GET /api/v1/videos` - List all videos (with optional status filter)

### System Management

- `GET /api/v1/health` - System health check
- `GET /api/v1/stats` - API usage statistics
- `POST /api/v1/cleanup` - Manually trigger cleanup of old videos

### Example Usage

**Create a video:**
```bash
curl -X POST "http://localhost:8000/api/v1/videos" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain the Pythagorean theorem with visual proof",
    "fps": 30,
    "duration_limit": 45
  }'
```

**Check status:**
```bash
curl "http://localhost:8000/api/v1/videos/{video_id}/status"
```

**Download video:**
```bash
curl -O "http://localhost:8000/api/v1/videos/{video_id}/download"
```

## Configuration

All configuration is managed through environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | 0.0.0.0 | Host to bind the API |
| `API_PORT` | 8000 | Port to run the API |
| `LOG_LEVEL` | INFO | Logging level |
| `VIDEOS_DIR` | generated_videos | Directory for storing videos |
| `TEMP_DIR` | /tmp/manim_videos | Temporary directory for processing |
| `MAX_CONCURRENT_VIDEOS` | 5 | Maximum concurrent video generations |
| `VIDEO_RETENTION_DAYS` | 7 | Days to keep videos before cleanup |

## Architecture

### Services

- **ScriptGenerator**: Handles AI-powered Manim script generation
- **VideoProcessor**: Manages Manim execution and video rendering
- **VideoStorage**: Manages video lifecycle and metadata

### Models

- **VideoRequest**: Input validation for video creation
- **VideoResponse**: API response format
- **VideoInfo**: Internal video metadata storage

### Features

- **Error Handling**: Comprehensive error handling with custom exceptions
- **Logging**: Structured logging throughout the application
- **Validation**: Input validation using Pydantic
- **Background Tasks**: Async video processing
- **Resource Management**: Automatic cleanup and limits

## Development

### Adding New Features

The modular architecture makes it easy to extend:

1. **New endpoints**: Add to `app/api/routes.py`
2. **New services**: Create in `app/services/`
3. **New models**: Add to `app/models/`
4. **Configuration**: Update `app/core/config.py`

### Database Integration

To add database storage:

1. Replace `VideoStorage` in `app/services/storage.py`
2. Add database models
3. Update dependencies in `app/api/dependencies.py`

### Queue System

To add Redis/Celery for better scalability:

1. Replace background tasks in `app/api/routes.py`
2. Create Celery workers
3. Update Docker Compose with Redis

## Monitoring

### Health Checks

- `GET /api/v1/health` provides system status
- Docker health checks included
- Monitors Manim and FFmpeg availability

### Logging

- Structured logging with timestamps
- Error tracking and debugging info
- Configurable log levels
