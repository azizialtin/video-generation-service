from app.services.storage import video_storage
from app.services.script_generator import ScriptGenerator
from app.services.video_processor import VideoProcessor

def get_video_storage():
    """Dependency for video storage service"""
    return video_storage

def get_script_generator():
    """Dependency for script generator service"""
    return ScriptGenerator()

def get_video_processor():
    """Dependency for video processor service"""
    return VideoProcessor()