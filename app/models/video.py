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
    prompt: str = Field(..., min_length=10, max_length=10000, description="Description of the educational video to generate")
    duration_limit: Optional[int] = Field(default=30, ge=5, le=1200, description="Maximum duration in seconds")

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