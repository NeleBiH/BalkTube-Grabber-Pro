"""Background worker threads for search, thumbnail, and download operations."""

import os
import logging
import requests
from PySide6.QtCore import QThread
from PySide6.QtGui import QPixmap
import yt_dlp

from .models import WorkerSignals, DownloadItem
from .constants import THUMBNAIL_SEMAPHORE

log = logging.getLogger("BalkGrab")


class SearchWorker(QThread):
    """Search thread to keep GUI responsive"""

    def __init__(self, query: str, signals: WorkerSignals, count: int = 10):
        super().__init__()
        self.query = query
        self.signals = signals
        self.count = count

    def run(self):
        log.info(f"Starting search: '{self.query}' (count={self.count})")
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'default_search': f'ytsearch{self.count}',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info(f"ytsearch{self.count}:{self.query}", download=False)

            if results and 'entries' in results:
                videos = []
                for i, entry in enumerate(results['entries']):
                    if not entry:
                        continue
                    video_id = entry.get('id', '')
                    entry_type = entry.get('_type', 'url')
                    if entry_type == 'playlist':
                        log.debug(f"  [{i+1}] Skipping channel/playlist result: {entry.get('title', '')[:40]}")
                        continue
                    if video_id and (
                        (video_id.startswith('UC') and len(video_id) == 24) or
                        video_id.startswith('PL')
                    ):
                        log.debug(f"  [{i+1}] Skipping channel/playlist ID: {video_id}")
                        continue
                    if video_id:
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                    else:
                        video_url = entry.get('url', '')
                    video = {
                        'id': video_id,
                        'title': entry.get('title', 'Unknown'),
                        'url': video_url,
                        'thumbnail': entry.get('thumbnail', entry.get('thumbnails', [{}])[0].get('url', '') if entry.get('thumbnails') else ''),
                        'duration': entry.get('duration', 0),
                        'channel': entry.get('channel', entry.get('uploader', 'Unknown')),
                        'view_count': entry.get('view_count', 0),
                    }
                    videos.append(video)
                    log.debug(f"  [{i+1}] {video['title'][:40]}...")

                log.info(f"Found {len(videos)} videos")
                self.signals.search_results.emit(videos)
            else:
                log.warning("No results")
                self.signals.search_results.emit([])

        except Exception as e:
            log.error(f"Search error: {str(e)}")
            self.signals.error.emit("search", f"Search error: {str(e)}")


class ThumbnailWorker(QThread):
    """Thread for downloading thumbnails"""

    def __init__(self, index: int, url: str, signals: WorkerSignals):
        super().__init__()
        self.index = index
        self.url = url
        self.signals = signals

    def run(self):
        try:
            if self.url:
                THUMBNAIL_SEMAPHORE.acquire()
                try:
                    response = requests.get(self.url, timeout=10)
                    if response.status_code == 200:
                        pixmap = QPixmap()
                        if pixmap.loadFromData(response.content):
                            self.signals.thumbnail_ready.emit(self.index, pixmap)
                finally:
                    THUMBNAIL_SEMAPHORE.release()
        except Exception as e:
            log.error(f"Thumbnail [{self.index}] error: {e}")


class DownloadWorker(QThread):
    """Thread for downloading video/audio"""

    def __init__(self, download_item: DownloadItem, signals: WorkerSignals,
                 cookies_browser: str = "", embed_metadata: bool = True, speed_limit: int = 0):
        super().__init__()
        self.item = download_item
        self.signals = signals
        self.cookies_browser = cookies_browser
        self.embed_metadata = embed_metadata
        self.speed_limit = speed_limit
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def postprocessor_hook(self, d):
        if self._cancelled and d.get('status') == 'started':
            raise Exception("Download cancelled by user")

    def progress_hook(self, d):
        if self._cancelled:
            raise Exception("Download cancelled by user")
        if d['status'] == 'downloading':
            if 'downloaded_bytes' in d and 'total_bytes' in d and d['total_bytes'] > 0:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                self.signals.progress.emit(self.item.id, percent, "downloading")
            elif '_percent_str' in d:
                try:
                    percent = float(d['_percent_str'].strip().replace('%', ''))
                    self.signals.progress.emit(self.item.id, percent, "downloading")
                except Exception:
                    pass
        elif d['status'] == 'finished':
            self.signals.progress.emit(self.item.id, 95, "processing")

    def run(self):
        try:
            output_template = os.path.join(self.item.output_path, '%(title)s.%(ext)s')

            cookies_opts = {}
            if self.cookies_browser:
                cookies_opts['cookiesfrombrowser'] = (self.cookies_browser,)

            if self.item.format_type == 'audio':
                audio_formats = {
                    'MP3 - 320kbps': ('mp3', '320'),
                    'MP3 - 256kbps': ('mp3', '256'),
                    'MP3 - 192kbps': ('mp3', '192'),
                    'MP3 - 128kbps': ('mp3', '128'),
                    'AAC - 256kbps': ('aac', '256'),
                    'AAC - 192kbps': ('aac', '192'),
                    'FLAC (lossless)': ('flac', '0'),
                    'WAV (lossless)': ('wav', '0'),
                    'OGG - 320kbps': ('vorbis', '320'),
                    'OGG - 192kbps': ('vorbis', '192'),
                }

                codec, bitrate = audio_formats.get(self.item.quality, ('mp3', '192'))

                postprocessors = [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': codec, 'preferredquality': bitrate},
                ]
                if self.embed_metadata:
                    postprocessors += [
                        {'key': 'FFmpegMetadata', 'add_metadata': True},
                        {'key': 'EmbedThumbnail'},
                    ]

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': output_template,
                    'progress_hooks': [self.progress_hook],
                    'postprocessor_hooks': [self.postprocessor_hook],
                    'postprocessors': postprocessors,
                    'writethumbnail': self.embed_metadata,
                    'prefer_ffmpeg': True,
                    'noplaylist': True,
                    'socket_timeout': 30,
                    'fragment_retries': 3,
                    'remote_components': ['ejs:github'],
                    **cookies_opts,
                }
                if self.speed_limit > 0:
                    ydl_opts['ratelimit'] = self.speed_limit * 1024
            else:
                resolution_formats = {
                    'Best quality': 'bestvideo+bestaudio/best',
                    'Najbolja kvaliteta': 'bestvideo+bestaudio/best',
                    'Beste Qualität': 'bestvideo+bestaudio/best',
                    '2160p (4K)': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]/best',
                    '1440p (2K)': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]/best',
                    '1080p (Full HD)': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
                    '720p (HD)': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
                    '480p': 'bestvideo[height<=480]+bestaudio/best[height<=480]/best',
                    '360p': 'bestvideo[height<=360]+bestaudio/best[height<=360]/best',
                    '240p': 'bestvideo[height<=240]+bestaudio/best[height<=240]/best',
                }

                format_str = resolution_formats.get(self.item.quality, 'bestvideo+bestaudio/best')

                ydl_opts = {
                    'format': format_str,
                    'outtmpl': output_template,
                    'progress_hooks': [self.progress_hook],
                    'postprocessor_hooks': [self.postprocessor_hook],
                    'merge_output_format': 'mp4',
                    'noplaylist': True,
                    'socket_timeout': 30,
                    'fragment_retries': 3,
                    'remote_components': ['ejs:github'],
                    **cookies_opts,
                }
                if self.speed_limit > 0:
                    ydl_opts['ratelimit'] = self.speed_limit * 1024

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.item.url, download=True)

                base_filepath = ydl.prepare_filename(info)
                if self.item.format_type == 'audio':
                    codec = audio_formats.get(self.item.quality, ('mp3', '192'))[0]
                    if codec == 'vorbis':
                        codec = 'ogg'
                    filepath = os.path.splitext(base_filepath)[0] + f".{codec}"
                else:
                    filepath = os.path.splitext(base_filepath)[0] + ".mp4"

            self.signals.progress.emit(self.item.id, 100, "done")
            self.signals.finished.emit(self.item.id, "done", filepath)

        except Exception as e:
            error_msg = str(e)
            if "Requested format is not available" in error_msg:
                error_msg = "Video unavailable or format restricted (private/deleted/geo-blocked)"
            log.error(f"Download error: {error_msg}", exc_info=True)
            self.signals.error.emit(self.item.id, error_msg)
