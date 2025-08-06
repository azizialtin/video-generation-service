#
#  Copyright 2025 AI Edge Eliza
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
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