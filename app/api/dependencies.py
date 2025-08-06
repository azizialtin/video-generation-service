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