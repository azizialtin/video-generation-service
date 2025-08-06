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
from pydantic_settings import BaseSettings
import os
import platform
from dotenv import load_dotenv

load_dotenv()

def get_temp_dir() -> str:
    """Platform-specific temp directory"""
    if platform.system() == "Windows":
        return os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp", "manim_videos")
    else:
        return "/tmp/manim_videos"


class Settings(BaseSettings):
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    LOG_LEVEL: str = "DEBUG"

    # Azure Settings (for TTS voiceover)
    AZURE_SUBSCRIPTION_KEY: str = os.getenv("AZURE_SUBSCRIPTION_KEY")
    AZURE_SERVICE_REGION: str = os.getenv("AZURE_SERVICE_REGION")

    # Gemini Settings
    GEMINI_API_KEY: str = ""

    # Storage Settings - Fixed for Windows compatibility
    VIDEOS_DIR: str = "generated_videos"
    TEMP_DIR: str = get_temp_dir()

    # Video Settings
    MAX_VIDEO_DURATION: int = 30  # 0.5 minutes - content duration limit
    MANIM_PROCESSING_TIMEOUT: int = 300  # 5 minutes for regular videos
    CLEANUP_INTERVAL: int = 3600  # 1 hour

    # Performance Settings
    MAX_CONCURRENT_VIDEOS: int = 2  # Reduced further for voiceover stability
    VIDEO_RETENTION_DAYS: int = 7

    class Config:
        env_file = ".env"


settings = Settings()