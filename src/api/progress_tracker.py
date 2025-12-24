"""
Progress Tracker for EDA Pipeline
Provides real-time status updates for the frontend.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
import threading

# Thread-safe lock for status updates
_lock = threading.Lock()

# Stages configuration
STAGES = [
    {"id": "profiling", "name": "Data Profiling", "progress_start": 10, "progress_end": 20},
    {"id": "cleaning", "name": "Data Cleaning", "progress_start": 20, "progress_end": 35},
    {"id": "visualization", "name": "Visualization", "progress_start": 35, "progress_end": 50},
    {"id": "statistics", "name": "Statistical Analysis", "progress_start": 50, "progress_end": 65},
    {"id": "ml_xai", "name": "ML & XAI Analysis", "progress_start": 65, "progress_end": 85},
    {"id": "report", "name": "Report Generation", "progress_start": 85, "progress_end": 100},
]

class ProgressTracker:
    """Tracks and reports pipeline progress to the API."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.reset()
    
    def reset(self):
        """Reset tracker to initial state."""
        with _lock:
            self._status = "idle"
            self._message = ""
            self._progress = 0
            self._current_stage = None
            self._stages = [
                {"id": s["id"], "name": s["name"], "status": "pending"}
                for s in STAGES
            ]
            self._activity_log: List[Dict[str, Any]] = []
    
    def start(self):
        """Start the analysis."""
        with _lock:
            self._status = "running"
            self._message = "Starting EDA pipeline..."
            self._progress = 5
            self._activity_log = []
    
    def start_stage(self, stage_id: str):
        """Mark a stage as running."""
        with _lock:
            self._current_stage = stage_id
            for stage in self._stages:
                if stage["id"] == stage_id:
                    stage["status"] = "running"
                    self._message = f"Running {stage['name']}..."
                    # Set progress to stage start
                    for s in STAGES:
                        if s["id"] == stage_id:
                            self._progress = s["progress_start"]
                            break
                    break
    
    def complete_stage(self, stage_id: str):
        """Mark a stage as completed."""
        with _lock:
            for stage in self._stages:
                if stage["id"] == stage_id:
                    stage["status"] = "completed"
                    # Set progress to stage end
                    for s in STAGES:
                        if s["id"] == stage_id:
                            self._progress = s["progress_end"]
                            break
                    break
    
    def log_activity(self, agent: str, action: str, status: str = "completed"):
        """Log an agent activity."""
        with _lock:
            entry = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "agent": agent,
                "action": action,
                "status": status
            }
            # Keep most recent first, limit to 20 entries
            self._activity_log.insert(0, entry)
            if len(self._activity_log) > 20:
                self._activity_log = self._activity_log[:20]
    
    def complete(self):
        """Mark analysis as complete."""
        with _lock:
            self._status = "completed"
            self._message = "Analysis complete!"
            self._progress = 100
            self._current_stage = None
            for stage in self._stages:
                stage["status"] = "completed"
    
    def error(self, message: str):
        """Mark analysis as failed."""
        with _lock:
            self._status = "error"
            self._message = message
            self._progress = 0
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status for API response."""
        with _lock:
            return {
                "status": self._status,
                "message": self._message,
                "progress": self._progress,
                "current_stage": self._current_stage,
                "stages": self._stages.copy(),
                "activity_log": self._activity_log.copy()
            }


# Singleton instance
tracker = ProgressTracker()
