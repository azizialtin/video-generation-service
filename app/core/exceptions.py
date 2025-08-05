from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class VideoGenerationError(Exception):
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)


class VideoNotFoundError(Exception):
    pass


class VideoProcessingError(VideoGenerationError):
    pass


class ScriptGenerationError(VideoGenerationError):
    pass


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(VideoNotFoundError)
    async def video_not_found_handler(request: Request, exc: VideoNotFoundError):
        return JSONResponse(
            status_code=404,
            content={"error": "Video not found", "detail": str(exc)}
        )

    @app.exception_handler(VideoGenerationError)
    async def video_generation_handler(request: Request, exc: VideoGenerationError):
        logger.error(f"Video generation error: {exc.message} - {exc.details}")
        return JSONResponse(
            status_code=500,
            content={"error": exc.message, "detail": exc.details}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unexpected error: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": "An unexpected error occurred"}
        )