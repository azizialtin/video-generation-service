from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime

class VideoStatus(str, Enum):
    QUEUED = "queued"
    GENERATING_SCRIPT = "generating_script"
    RENDERING_VIDEO = "rendering_video"
    COMPLETED = "completed"
    FAILED = "failed"

class VideoRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=1000, description="Description of the educational video to generate")
    duration_limit: Optional[int] = Field(default=30, ge=5, le=120, description="Maximum duration in seconds")

class VideoResponse(BaseModel):
    video_id: str
    status: VideoStatus
    message: str
    video_url: Optional[str] = None
    created_at: datetime
    progress: Optional[int] = Field(default=0, ge=0, le=100, description="Generation progress percentage")

class VideoInfo(BaseModel):
    video_id: str
    status: VideoStatus
    message: str
    video_path: Optional[str] = None
    created_at: datetime
    script_content: Optional[str] = None
    error_details: Optional[str] = None
    progress: int = 0