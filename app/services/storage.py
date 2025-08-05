from typing import Dict, Optional, List
from app.models.video import VideoInfo, VideoStatus
from app.core.config import settings
from app.core.exceptions import VideoNotFoundError
import os
import logging
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


class VideoStorage:
    def __init__(self):
        self._videos: Dict[str, VideoInfo] = {}
        self._lock = threading.Lock()
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(settings.VIDEOS_DIR, exist_ok=True)
        os.makedirs(settings.TEMP_DIR, exist_ok=True)

    def create_video(self, video_id: str, prompt: str) -> VideoInfo:
        """Create a new video entry"""
        with self._lock:
            video_info = VideoInfo(
                video_id=video_id,
                status=VideoStatus.QUEUED,
                message="Video generation queued",
                created_at=datetime.utcnow()
            )
            self._videos[video_id] = video_info
            return video_info

    def get_video(self, video_id: str) -> VideoInfo:
        """Get video information"""
        with self._lock:
            if video_id not in self._videos:
                raise VideoNotFoundError(f"Video {video_id} not found")
            return self._videos[video_id]

    def update_video(self, video_id: str, **updates) -> VideoInfo:
        """Update video information"""
        with self._lock:
            # Don't call self.get_video() - do the check directly here
            if video_id not in self._videos:
                raise VideoNotFoundError(f"Video {video_id} not found")

            video_info = self._videos[video_id]
            for key, value in updates.items():
                if hasattr(video_info, key):
                    setattr(video_info, key, value)
            return video_info

    def delete_video(self, video_id: str) -> bool:
        """Delete video and associated files"""
        with self._lock:
            try:
                video_info = self.get_video(video_id)

                # Remove video file if exists
                if video_info.video_path and os.path.exists(video_info.video_path):
                    os.remove(video_info.video_path)
                    logger.info(f"Deleted video file: {video_info.video_path}")

                # Remove from memory
                del self._videos[video_id]
                return True

            except VideoNotFoundError:
                return False

    def list_videos(self, status: Optional[VideoStatus] = None) -> List[VideoInfo]:
        """List all videos, optionally filtered by status"""
        with self._lock:
            videos = list(self._videos.values())
            if status:
                videos = [v for v in videos if v.status == status]
            return sorted(videos, key=lambda x: x.created_at, reverse=True)

    def cleanup_old_videos(self):
        """Clean up videos older than retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=settings.VIDEO_RETENTION_DAYS)
        videos_to_delete = []

        with self._lock:
            videos_to_delete = [
                video_id for video_id, video_info in self._videos.items()
                if video_info.created_at < cutoff_date
            ]

        for video_id in videos_to_delete:
            self.delete_video(video_id)
            logger.info(f"Cleaned up old video: {video_id}")

    def get_active_video_count(self) -> int:
        """Get count of videos currently being processed"""
        with self._lock:
            active_statuses = {VideoStatus.QUEUED, VideoStatus.GENERATING_SCRIPT, VideoStatus.RENDERING_VIDEO}
            return sum(1 for v in self._videos.values() if v.status in active_statuses)

    def get_stats(self) -> Dict:
        """Get storage statistics"""
        with self._lock:
            total_videos = len(self._videos)
            status_counts = {}
            for status in VideoStatus:
                status_counts[status.value] = sum(1 for v in self._videos.values() if v.status == status)

            return {
                "total_videos": total_videos,
                "active_videos": self.get_active_video_count(),
                "status_breakdown": status_counts
            }


# Global storage instance
video_storage = VideoStorage()