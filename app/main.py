from fastapi import FastAPI
from app.api.routes import router
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Manim Video Generator API",
        description="Generate educational videos using Manim",
        version="1.0.0"
    )

    # Setup exception handlers
    setup_exception_handlers(app)

    # Include routers
    app.include_router(router, prefix="/api/v1")

    # Health check endpoint at root
    @app.get("/")
    async def root():
        return {"message": "Manim Video Generator API", "version": "1.0.0", "status": "running"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    import os

    # Create directories
    os.makedirs(settings.VIDEOS_DIR, exist_ok=True)
    os.makedirs(settings.TEMP_DIR, exist_ok=True)

    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)