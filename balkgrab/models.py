"""Data models and signal definitions."""

from datetime import datetime
from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QPixmap


class WorkerSignals(QObject):
    """Signals for communication between worker threads and GUI"""
    progress = Signal(str, float, str)      # download_id, percentage, message
    finished = Signal(str, str, str)         # download_id, status, filepath
    error = Signal(str, str)                 # download_id, error message
    search_results = Signal(list)            # list of search results
    thumbnail_ready = Signal(int, QPixmap)   # index, pixmap
    playlist_info = Signal(str, list)        # original_url, list of video dicts


class DownloadItem:
    """Represents a single download"""
    def __init__(self, url: str, title: str, output_path: str,
                 format_type: str, quality: str):
        self.id = f"{datetime.now().strftime('%H%M%S%f')}_{hash(url) % 10000}"
        self.url = url
        self.title = title
        self.output_path = output_path
        self.format_type = format_type
        self.quality = quality
        self.progress = 0.0
        self.status = "waiting"  # waiting, downloading, processing, done, error
        self.filepath = ""
        self.error_message = ""
        self.created_at = datetime.now()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'output_path': self.output_path,
            'format_type': self.format_type,
            'quality': self.quality,
            'progress': self.progress,
            'status': self.status,
            'filepath': self.filepath,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'DownloadItem':
        item = cls(
            url=data['url'],
            title=data['title'],
            output_path=data['output_path'],
            format_type=data['format_type'],
            quality=data['quality']
        )
        item.id = data['id']
        item.progress = data.get('progress', 0.0)
        item.status = data.get('status', 'done')
        item.filepath = data.get('filepath', '')
        item.error_message = data.get('error_message', '')
        if 'created_at' in data:
            item.created_at = datetime.fromisoformat(data['created_at'])
        return item
