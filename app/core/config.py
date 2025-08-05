from pydantic_settings import BaseSettings
import os
import platform


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

    # Azure Settings (for TTS voiceover) - keeping for future use
    AZURE_SUBSCRIPTION_KEY: str = ""
    AZURE_SERVICE_REGION: str = ""

    # Gemini Settings
    GEMINI_API_KEY: str = ""

    # Storage Settings - Fixed for Windows compatibility
    VIDEOS_DIR: str = "generated_videos"
    TEMP_DIR: str = get_temp_dir()

    # Video Settings
    MAX_VIDEO_DURATION: int = 30  # 0.5 minutes - content duration limit
    MANIM_PROCESSING_TIMEOUT: int = 300  # 5 minutes - reduced for testing
    CLEANUP_INTERVAL: int = 3600  # 1 hour

    # Performance Settings
    MAX_CONCURRENT_VIDEOS: int = 3  # Reduced for stability
    VIDEO_RETENTION_DAYS: int = 7

    class Config:
        env_file = ".env"


settings = Settings()