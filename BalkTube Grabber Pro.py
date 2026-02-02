"""
🎵 BalkTube Grabber Pro v2.0 - ClipGrab klon kako treba! 🎵
- PySide6 GUI sa tabovima
- Pretraga YouTube videa
- Download manager sa napretkom
- Integrirani media player
- System tray podrška
- Multi-language (EN/DE/HR)

INSTALACIJA:
pip install PySide6 yt-dlp requests

TAKOĐER TREBAŠ:
ffmpeg - za audio konverziju
"""

import sys
import os
import json
import threading
import requests
import logging
from datetime import datetime

# Add deno to PATH if available (needed for yt-dlp signature solving)
deno_path = os.path.expanduser("~/.deno/bin")
if os.path.isdir(deno_path):
    os.environ["PATH"] = deno_path + os.pathsep + os.environ.get("PATH", "")
from pathlib import Path
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QProgressBar,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QGroupBox, QRadioButton, QButtonGroup, QFrame, QSplitter,
    QStackedWidget, QSizePolicy, QScrollArea, QTabWidget,
    QSlider, QCheckBox, QTextEdit, QSystemTrayIcon, QMenu,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox, QInputDialog
)
from PySide6.QtCore import (
    Qt, Signal, QObject, QSize, QThread, QMetaObject, Q_ARG,
    Slot, QUrl, QTimer, QSettings
)
from PySide6.QtGui import (
    QPixmap, QFont, QIcon, QPalette, QColor, QAction, QDesktopServices
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

import yt_dlp

# ============ DEBUG LOGGING ============
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger("BalkTube")

# ============ APP DIRECTORY ============
APP_DIR = os.path.dirname(os.path.abspath(__file__))


# ============ CLICKABLE SLIDER ============
class ClickableSlider(QSlider):
    """Slider that responds to clicks at the clicked position"""

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Emit sliderPressed FIRST so the flag gets set before position update
            self.sliderPressed.emit()

            # Calculate value from click position
            if self.orientation() == Qt.Horizontal:
                value = self.minimum() + (self.maximum() - self.minimum()) * event.position().x() / self.width()
            else:
                value = self.minimum() + (self.maximum() - self.minimum()) * (self.height() - event.position().y()) / self.height()
            self.setValue(int(value))
            self.sliderMoved.emit(int(value))
            event.accept()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Emit sliderReleased to finalize the seek
            self.sliderReleased.emit()
        super().mouseReleaseEvent(event)

# ============ VERSION INFO ============
APP_VERSION = "0.1.0 Alpha"
APP_NAME = "BalkTube Grabber Pro"

# ============ TRANSLATIONS ============
TRANSLATIONS = {
    'en': {
        'app_title': '🎵 BalkTube Grabber Pro',
        'tab_search': '🔍 Search',
        'tab_downloads': '⬇️ Downloads',
        'tab_settings': '⚙️ Settings',
        'tab_about': 'ℹ️ About',
        'search_placeholder': '🔍 Search YouTube or paste URL...',
        'search_btn': '🔍 Search',
        'searching': '⏳ Searching...',
        'results': '📋 Search Results',
        'preview': '📺 Preview',
        'select_video': 'Select video from list',
        'no_video_selected': 'No video selected',
        'format': '⚙️ Format',
        'video': '🎬 Video',
        'audio': '🎵 Audio',
        'quality': 'Quality:',
        'status': '📊 Status',
        'waiting': 'Waiting for selection... 👀',
        'download_btn': '⬇️  DOWNLOAD NOW!  ⬇️',
        'found_videos': 'Found {count} videos! 🎉',
        'no_results': 'No results 😢',
        'ready_download': 'Ready to download! 🚀',
        'downloading': 'Downloading... {percent:.1f}%',
        'processing': 'Processing... ⏳',
        'done': 'Done! ✅',
        'error': 'Error! ❌',
        'output_folder': '📁 Output Folder',
        'browse': 'Browse...',
        'best_quality': 'Best quality',
        # Downloads tab
        'downloads_title': '⬇️ Download Manager',
        'no_downloads': 'No downloads yet.\nSearch and download some music! 🎵',
        'filename': 'Filename',
        'progress': 'Progress',
        'status_col': 'Status',
        'actions': 'Actions',
        'clear_completed': '🗑️ Clear Completed',
        'open_folder': '📂 Open Folder',
        # Player
        'player_title': '🎵 Media Player',
        'now_playing': 'Now Playing:',
        'nothing_playing': 'Nothing playing',
        # Settings
        'settings_title': '⚙️ Settings',
        'language': 'Language:',
        'appearance': 'Appearance',
        'system_tray': 'Show system tray icon',
        'minimize_tray': 'Minimize to system tray',
        'start_minimized': 'Start minimized',
        'notifications': 'Show download notifications',
        'downloads_settings': 'Downloads',
        'simultaneous': 'Simultaneous downloads:',
        'auto_play': 'Auto-play after download',
        'save_settings': '💾 Save Settings',
        'settings_saved': 'Settings saved! ✅',
        # About
        'about_title': 'About BalkTube Grabber Pro',
        'about_description': '''
<h2>🎵 BalkTube Grabber Pro</h2>
<p><b>Version:</b> {version}</p>

<h3>What is this?</h3>
<p>BalkTube Grabber Pro is a free, open-source YouTube downloader inspired by ClipGrab.
Download videos in various resolutions or convert them to audio formats like MP3, FLAC, and more!</p>

<h3>Features</h3>
<ul>
<li>🔍 Search YouTube directly from the app</li>
<li>📺 Preview videos before downloading</li>
<li>🎬 Download videos in resolutions from 240p to 4K</li>
<li>🎵 Convert to audio: MP3, AAC, FLAC, WAV, OGG</li>
<li>⬇️ Download manager with progress tracking</li>
<li>🎧 Built-in media player</li>
<li>🌍 Multi-language support</li>
<li>🖥️ System tray integration</li>
</ul>

<h3>Technologies</h3>
<ul>
<li><b>GUI:</b> PySide6 (Qt for Python)</li>
<li><b>Backend:</b> yt-dlp</li>
<li><b>Audio/Video:</b> FFmpeg</li>
</ul>
''',
        'license_title': '📜 License',
        'license_text': '''
<h3>MIT License</h3>
<p>Copyright (c) 2024-2026 BalkTube Team</p>

<p>Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:</p>

<p>The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.</p>

<p><b>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.</b></p>

<h3>Third-party Licenses</h3>
<ul>
<li><b>PySide6:</b> LGPL v3</li>
<li><b>yt-dlp:</b> Unlicense (Public Domain)</li>
<li><b>requests:</b> Apache 2.0</li>
<li><b>FFmpeg:</b> LGPL v2.1+ / GPL v2+</li>
</ul>

<p>All third-party licenses are compatible with this MIT license.</p>
''',
        'links_title': '🔗 Links',
        'github': '⭐ GitHub Repository',
        'report_bug': '🐛 Report a Bug',
        'footer': 'Made with ❤️,Claude code and some coffee | Balkan Edition 🇧🇦🇭🇷🇷🇸'
    },
    'de': {
        'app_title': '🎵 BalkTube Grabber Pro',
        'tab_search': '🔍 Suchen',
        'tab_downloads': '⬇️ Downloads',
        'tab_settings': '⚙️ Einstellungen',
        'tab_about': 'ℹ️ Über',
        'search_placeholder': '🔍 YouTube durchsuchen oder URL einfügen...',
        'search_btn': '🔍 Suchen',
        'searching': '⏳ Suche...',
        'results': '📋 Suchergebnisse',
        'preview': '📺 Vorschau',
        'select_video': 'Video aus Liste auswählen',
        'no_video_selected': 'Kein Video ausgewählt',
        'format': '⚙️ Format',
        'video': '🎬 Video',
        'audio': '🎵 Audio',
        'quality': 'Qualität:',
        'status': '📊 Status',
        'waiting': 'Warte auf Auswahl... 👀',
        'download_btn': '⬇️  JETZT HERUNTERLADEN!  ⬇️',
        'found_videos': '{count} Videos gefunden! 🎉',
        'no_results': 'Keine Ergebnisse 😢',
        'ready_download': 'Bereit zum Download! 🚀',
        'downloading': 'Herunterladen... {percent:.1f}%',
        'processing': 'Verarbeitung... ⏳',
        'done': 'Fertig! ✅',
        'error': 'Fehler! ❌',
        'output_folder': '📁 Ausgabeordner',
        'browse': 'Durchsuchen...',
        'best_quality': 'Beste Qualität',
        'downloads_title': '⬇️ Download-Manager',
        'no_downloads': 'Noch keine Downloads.\nSuche und lade Musik herunter! 🎵',
        'filename': 'Dateiname',
        'progress': 'Fortschritt',
        'status_col': 'Status',
        'actions': 'Aktionen',
        'clear_completed': '🗑️ Abgeschlossene löschen',
        'open_folder': '📂 Ordner öffnen',
        'player_title': '🎵 Mediaplayer',
        'now_playing': 'Wird abgespielt:',
        'nothing_playing': 'Nichts wird abgespielt',
        'settings_title': '⚙️ Einstellungen',
        'language': 'Sprache:',
        'appearance': 'Aussehen',
        'system_tray': 'Taskleistensymbol anzeigen',
        'minimize_tray': 'In Taskleiste minimieren',
        'start_minimized': 'Minimiert starten',
        'notifications': 'Download-Benachrichtigungen anzeigen',
        'downloads_settings': 'Downloads',
        'simultaneous': 'Gleichzeitige Downloads:',
        'auto_play': 'Nach Download automatisch abspielen',
        'save_settings': '💾 Einstellungen speichern',
        'settings_saved': 'Einstellungen gespeichert! ✅',
        'about_title': 'Über BalkTube Grabber Pro',
        'about_description': '''
<h2>🎵 BalkTube Grabber Pro</h2>
<p><b>Version:</b> {version}</p>

<h3>Was ist das?</h3>
<p>BalkTube Grabber Pro ist ein kostenloser, Open-Source YouTube-Downloader inspiriert von ClipGrab.
Laden Sie Videos in verschiedenen Auflösungen herunter oder konvertieren Sie sie in Audioformate wie MP3, FLAC und mehr!</p>

<h3>Funktionen</h3>
<ul>
<li>🔍 YouTube direkt in der App durchsuchen</li>
<li>📺 Videos vor dem Download ansehen</li>
<li>🎬 Videos in Auflösungen von 240p bis 4K herunterladen</li>
<li>🎵 In Audio konvertieren: MP3, AAC, FLAC, WAV, OGG</li>
<li>⬇️ Download-Manager mit Fortschrittsverfolgung</li>
<li>🎧 Integrierter Mediaplayer</li>
<li>🌍 Mehrsprachige Unterstützung</li>
<li>🖥️ Taskleisten-Integration</li>
</ul>
''',
        'license_title': '📜 Lizenz',
        'links_title': '🔗 Links',
        'github': '⭐ GitHub Repository',
        'report_bug': '🐛 Fehler melden',
        'footer': 'Mit ❤️ und etwas Ćevapi gemacht | Balkan Edition 🇧🇦🇭🇷🇷🇸'
    },
    'hr': {
        'app_title': '🎵 BalkTube Grabber Pro',
        'tab_search': '🔍 Traži',
        'tab_downloads': '⬇️ Preuzimanja',
        'tab_settings': '⚙️ Postavke',
        'tab_about': 'ℹ️ O aplikaciji',
        'search_placeholder': '🔍 Pretraži YouTube ili zalijepi URL...',
        'search_btn': '🔍 Pretraži',
        'searching': '⏳ Tražim...',
        'results': '📋 Rezultati pretrage',
        'preview': '📺 Preview',
        'select_video': 'Odaberi video iz liste',
        'no_video_selected': 'Nije odabran video',
        'format': '⚙️ Format',
        'video': '🎬 Video',
        'audio': '🎵 Audio',
        'quality': 'Kvaliteta:',
        'status': '📊 Status',
        'waiting': 'Čekam da odabereš... 👀',
        'download_btn': '⬇️  SKINI ODMAH!  ⬇️',
        'found_videos': 'Pronađeno {count} videa! 🎉',
        'no_results': 'Nema rezultata 😢',
        'ready_download': 'Spremno za skidanje! 🚀',
        'downloading': 'Skidam... {percent:.1f}%',
        'processing': 'Obrađujem... ⏳',
        'done': 'Gotovo! ✅',
        'error': 'Greška! ❌',
        'output_folder': '📁 Izlazna mapa',
        'browse': 'Odaberi...',
        'best_quality': 'Najbolja kvaliteta',
        'downloads_title': '⬇️ Upravitelj preuzimanja',
        'no_downloads': 'Nema preuzimanja.\nPretraži i skini neku muziku! 🎵',
        'filename': 'Naziv datoteke',
        'progress': 'Napredak',
        'status_col': 'Status',
        'actions': 'Akcije',
        'clear_completed': '🗑️ Očisti završene',
        'open_folder': '📂 Otvori mapu',
        'player_title': '🎵 Media Player',
        'now_playing': 'Sad svira:',
        'nothing_playing': 'Ništa ne svira',
        'settings_title': '⚙️ Postavke',
        'language': 'Jezik:',
        'appearance': 'Izgled',
        'system_tray': 'Prikaži ikonu u system trayu',
        'minimize_tray': 'Minimiziraj u system tray',
        'start_minimized': 'Pokreni minimizirano',
        'notifications': 'Prikaži obavijesti o preuzimanju',
        'downloads_settings': 'Preuzimanja',
        'simultaneous': 'Istovremena preuzimanja:',
        'auto_play': 'Automatski pusti nakon preuzimanja',
        'save_settings': '💾 Spremi postavke',
        'settings_saved': 'Postavke spremljene! ✅',
        'about_title': 'O aplikaciji BalkTube Grabber Pro',
        'about_description': '''
<h2>🎵 BalkTube Grabber Pro</h2>
<p><b>Verzija:</b> {version}</p>

<h3>Šta je ovo?</h3>
<p>BalkTube Grabber Pro je besplatan YouTube downloader otvorenog koda inspiriran ClipGrab-om.
Skidaj videe u raznim rezolucijama ili ih pretvori u audio formate kao MP3, FLAC i druge!</p>

<h3>Mogućnosti</h3>
<ul>
<li>🔍 Pretraži YouTube direktno iz aplikacije</li>
<li>📺 Pregledaj video prije skidanja</li>
<li>🎬 Skidaj videe u rezolucijama od 240p do 4K</li>
<li>🎵 Pretvori u audio: MP3, AAC, FLAC, WAV, OGG</li>
<li>⬇️ Upravitelj preuzimanja s praćenjem napretka</li>
<li>🎧 Ugrađeni media player</li>
<li>🌍 Višejezična podrška</li>
<li>🖥️ System tray integracija</li>
</ul>
''',
        'license_title': '📜 Licenca',
        'license_text': '''
<h3>MIT Licenca</h3>
<p>Copyright (c) 2024-2026 BalkTube Tim</p>

<p>Ovim se daje dozvola, besplatno, svakoj osobi koja dobije kopiju
ovog softvera i pripadajuće dokumentacije ("Softver"), da koristi
Softver bez ograničenja, uključujući bez ograničenja prava na korištenje,
kopiranje, modificiranje, spajanje, objavljivanje, distribuciju,
podlicenciranje i/ili prodaju kopija Softvera.</p>

<p><b>SOFTVER SE PRUŽA "KAKAV JEST", BEZ IKAKVE GARANCIJE.</b></p>

<h3>Licence trećih strana</h3>
<ul>
<li><b>PySide6:</b> LGPL v3</li>
<li><b>yt-dlp:</b> Unlicense (Javna domena)</li>
<li><b>requests:</b> Apache 2.0</li>
<li><b>FFmpeg:</b> LGPL v2.1+ / GPL v2+</li>
</ul>

<p>Sve licence trećih strana su kompatibilne s MIT licencom.</p>
''',
        'links_title': '🔗 Linkovi',
        'github': '⭐ GitHub Repozitorij',
        'report_bug': '🐛 Prijavi grešku',
        'footer': 'Napravljeno s ❤️ i malo kave | Balkan Edition 🇧🇦🇭🇷🇷🇸'
    }
}


# ============ WORKER SIGNALS ============
class WorkerSignals(QObject):
    """Signali za komunikaciju između threadova i GUI-a"""
    progress = Signal(str, float, str)  # download_id, procenat, poruka
    finished = Signal(str, str, str)  # download_id, status, filepath
    error = Signal(str, str)  # download_id, error message
    search_results = Signal(list)  # lista rezultata pretrage
    thumbnail_ready = Signal(int, QPixmap)  # index, pixmap


# ============ DOWNLOAD ITEM ============
class DownloadItem:
    """Predstavlja jedan download"""
    def __init__(self, url: str, title: str, output_path: str,
                 format_type: str, quality: str):
        self.id = f"{datetime.now().strftime('%H%M%S')}_{hash(url) % 10000}"
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
        """Convert to dictionary for JSON serialization"""
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
        """Create DownloadItem from dictionary"""
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


# ============ SEARCH WORKER ============
class SearchWorker(QThread):
    """Thread za pretragu da GUI ne blokira"""

    def __init__(self, query: str, signals: WorkerSignals):
        super().__init__()
        self.query = query
        self.signals = signals

    def run(self):
        log.info(f"🔍 Počinjem pretragu: '{self.query}'")
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'default_search': 'ytsearch10',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                results = ydl.extract_info(f"ytsearch10:{self.query}", download=False)

            if results and 'entries' in results:
                videos = []
                for i, entry in enumerate(results['entries']):
                    if entry:
                        video = {
                            'id': entry.get('id', ''),
                            'title': entry.get('title', 'Unknown'),
                            'url': entry.get('url', f"https://www.youtube.com/watch?v={entry.get('id', '')}"),
                            'thumbnail': entry.get('thumbnail', entry.get('thumbnails', [{}])[0].get('url', '') if entry.get('thumbnails') else ''),
                            'duration': entry.get('duration', 0),
                            'channel': entry.get('channel', entry.get('uploader', 'Unknown')),
                            'view_count': entry.get('view_count', 0),
                        }
                        videos.append(video)
                        log.debug(f"  [{i+1}] {video['title'][:40]}...")

                log.info(f"✅ Pronađeno {len(videos)} videa")
                self.signals.search_results.emit(videos)
            else:
                log.warning("⚠️ Nema rezultata")
                self.signals.search_results.emit([])

        except Exception as e:
            log.error(f"❌ Greška pri pretrazi: {str(e)}")
            self.signals.error.emit("search", f"Search error: {str(e)}")


# ============ THUMBNAIL WORKER ============
class ThumbnailWorker(QThread):
    """Thread za skidanje thumbnailova"""

    def __init__(self, index: int, url: str, signals: WorkerSignals):
        super().__init__()
        self.index = index
        self.url = url
        self.signals = signals

    def run(self):
        try:
            if self.url:
                log.debug(f"📷 Skidam thumbnail [{self.index}]")
                response = requests.get(self.url, timeout=10)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    if pixmap.loadFromData(response.content):
                        self.signals.thumbnail_ready.emit(self.index, pixmap)
        except Exception as e:
            log.error(f"❌ Thumbnail [{self.index}] error: {e}")


# ============ DOWNLOAD WORKER ============
class DownloadWorker(QThread):
    """Thread za skidanje videa/audija"""

    def __init__(self, download_item: DownloadItem, signals: WorkerSignals):
        super().__init__()
        self.item = download_item
        self.signals = signals

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            if 'downloaded_bytes' in d and 'total_bytes' in d and d['total_bytes'] > 0:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                self.signals.progress.emit(self.item.id, percent, "downloading")
            elif '_percent_str' in d:
                try:
                    percent = float(d['_percent_str'].strip().replace('%', ''))
                    self.signals.progress.emit(self.item.id, percent, "downloading")
                except:
                    pass
        elif d['status'] == 'finished':
            self.signals.progress.emit(self.item.id, 95, "processing")

    def run(self):
        try:
            output_template = os.path.join(self.item.output_path, '%(title)s.%(ext)s')

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

                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': output_template,
                    'progress_hooks': [self.progress_hook],
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': codec,
                        'preferredquality': bitrate,
                    }],
                    'prefer_ffmpeg': True,
                    'allow_remote_components': 'ejs:github',
                }
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
                    'merge_output_format': 'mp4',
                    'allow_remote_components': 'ejs:github',
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.item.url, download=True)
                title = info.get('title', 'Video')

                # Pronađi stvarni filepath
                if self.item.format_type == 'audio':
                    codec = audio_formats.get(self.item.quality, ('mp3', '192'))[0]
                    if codec == 'vorbis':
                        codec = 'ogg'
                    filepath = os.path.join(self.item.output_path, f"{title}.{codec}")
                else:
                    filepath = os.path.join(self.item.output_path, f"{title}.mp4")

            self.signals.progress.emit(self.item.id, 100, "done")
            self.signals.finished.emit(self.item.id, "done", filepath)

        except Exception as e:
            error_msg = str(e)
            log.error(f"❌ Download error: {error_msg}")
            self.signals.error.emit(self.item.id, error_msg)


# ============ VIDEO ITEM WIDGET ============
class VideoItemWidget(QWidget):
    """Custom widget za prikaz video rezultata"""

    def __init__(self, video_data: dict, parent=None):
        super().__init__(parent)
        self.video_data = video_data
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(160, 90)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                background-color: #3c3c3c;
                border-radius: 6px;
                font-size: 24px;
            }
        """)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setText("🎬")
        layout.addWidget(self.thumbnail_label)

        # Info
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)

        title_label = QLabel(self.video_data.get('title', 'Unknown'))
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 13px;")
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(40)
        info_layout.addWidget(title_label)

        channel = self.video_data.get('channel', 'Unknown')
        duration = self.video_data.get('duration', 0)
        if duration:
            duration = int(duration)
            duration_str = f"{duration // 60}:{duration % 60:02d}"
        else:
            duration_str = "N/A"

        meta_label = QLabel(f"📺 {channel}  |  ⏱️ {duration_str}")
        meta_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        info_layout.addWidget(meta_label)

        views = self.video_data.get('view_count', 0)
        if views:
            if views >= 1000000:
                views_str = f"👁️ {views / 1000000:.1f}M"
            elif views >= 1000:
                views_str = f"👁️ {views / 1000:.1f}K"
            else:
                views_str = f"👁️ {views}"
            views_label = QLabel(views_str)
            views_label.setStyleSheet("color: #888888; font-size: 11px;")
            info_layout.addWidget(views_label)

        info_layout.addStretch()
        layout.addWidget(info_widget, 1)
        self.setMinimumHeight(106)

    def set_thumbnail(self, pixmap: QPixmap):
        scaled = pixmap.scaled(160, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.thumbnail_label.setPixmap(scaled)

    def sizeHint(self):
        return QSize(400, 110)


# ============ MAIN WINDOW ============
class BalkTubeGrabber(QMainWindow):
    """Glavni prozor aplikacije"""

    def __init__(self):
        super().__init__()

        # Settings
        self.settings = QSettings("BalkTube", "GrabberPro")
        self.current_language = self.settings.value("language", "hr")
        self.tr = TRANSLATIONS[self.current_language]

        self.setWindowTitle(self.tr['app_title'])
        self.setMinimumSize(900, 750)
        self.resize(1100, 900)

        # Set window icon
        icon_path = os.path.join(APP_DIR, "Icons", "icon_256x256.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Downloads history file
        self.downloads_file = os.path.expanduser("~/.config/BalkTube/downloads.json")
        os.makedirs(os.path.dirname(self.downloads_file), exist_ok=True)

        # Variables
        self.output_path = self.settings.value("output_path", os.path.expanduser("~/Downloads"))
        self.signals = WorkerSignals()
        self.current_videos: List[Dict] = []
        self.selected_video: Optional[Dict] = None
        self.thumbnail_workers: List[ThumbnailWorker] = []
        self.downloads: Dict[str, DownloadItem] = {}
        self.download_workers: Dict[str, DownloadWorker] = {}

        # Media player for downloaded files
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.player_is_playing = False
        self.current_playing_download_id = None
        self.current_playing_btn = None
        self.external_player_process = None  # Track external player (mpv/vlc)

        # Preview player for streaming
        self.preview_player = QMediaPlayer()
        self.preview_audio_output = QAudioOutput()
        self.preview_player.setAudioOutput(self.preview_audio_output)
        self.preview_audio_output.setVolume(0.7)
        self.preview_is_playing = False
        self.preview_slider_pressed_flag = False

        # System tray
        self.tray_icon = None

        # Setup
        self.setup_dark_theme()
        self.setup_ui()
        self.setup_system_tray()
        self.connect_signals()

        # Load settings
        self.load_settings()

        # Load previous downloads
        self.load_downloads()

    def get_text(self, key: str, **kwargs) -> str:
        """Get translated text"""
        text = self.tr.get(key, TRANSLATIONS['en'].get(key, key))
        if kwargs:
            text = text.format(**kwargs)
        return text

    def setup_dark_theme(self):
        """Setup dark theme"""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                background-color: #1e1e1e;
            }
            QTabBar::tab {
                background-color: #2d2d2d;
                color: #888888;
                padding: 12px 24px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 13px;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #00ff88;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background-color: #3d3d3d;
            }
            QLineEdit {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                color: white;
            }
            QLineEdit:focus {
                border: 2px solid #00ff88;
            }
            QPushButton {
                background-color: #00ff88;
                color: #1a1a1a;
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00cc6a;
            }
            QPushButton:pressed {
                background-color: #009950;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #888888;
            }
            QPushButton#downloadBtn {
                background-color: #00ff88;
                color: #1a1a1a;
                font-size: 16px;
                font-weight: bold;
                padding: 15px 40px;
            }
            QPushButton#downloadBtn:hover {
                background-color: #00cc6a;
            }
            QPushButton#playBtn {
                background-color: #00ff88;
                font-size: 20px;
                padding: 10px 30px;
                min-width: 60px;
            }
            QPushButton#stopBtn {
                background-color: #ff4444;
                font-size: 16px;
                padding: 10px 20px;
            }
            QListWidget {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: #2d2d2d;
                border-radius: 6px;
                margin: 3px;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #00ff88;
                color: #1a1a1a;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
            QComboBox {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                min-width: 200px;
            }
            QComboBox:hover {
                border: 2px solid #00ff88;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                selection-background-color: #00ff88;
                selection-color: #1a1a1a;
            }
            QProgressBar {
                background-color: #2d2d2d;
                border: none;
                border-radius: 8px;
                height: 20px;
                text-align: center;
                color: #1a1a1a;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #00ff88;
                border-radius: 8px;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #3d3d3d;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }
            QRadioButton, QCheckBox {
                font-size: 13px;
                spacing: 8px;
            }
            QRadioButton::indicator, QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QRadioButton::indicator:checked, QCheckBox::indicator:checked {
                background-color: #00ff88;
                border: 2px solid #00ff88;
                border-radius: 9px;
            }
            QRadioButton::indicator:unchecked, QCheckBox::indicator:unchecked {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 9px;
            }
            QCheckBox::indicator {
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                border-radius: 4px;
            }
            QSlider::groove:horizontal {
                background: #3d3d3d;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #00ff88;
                width: 16px;
                height: 16px;
                margin: -4px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background: #00ff88;
                border-radius: 4px;
            }
            QTableWidget {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                gridline-color: #3d3d3d;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #00ff88;
                color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #00ff88;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                padding: 10px;
            }
            QSpinBox {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #00ff88;
                border: none;
                width: 20px;
            }
            QSpinBox::up-button {
                border-top-right-radius: 6px;
            }
            QSpinBox::down-button {
                border-bottom-right-radius: 6px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #00cc6a;
            }
            QSpinBox::up-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-bottom: 6px solid white;
                width: 0;
                height: 0;
            }
            QSpinBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid white;
                width: 0;
                height: 0;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #00ff88;
                border-radius: 6px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #00cc6a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
                background: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: #2d2d2d;
            }
            QScrollBar:horizontal {
                background-color: #2d2d2d;
                height: 12px;
                border-radius: 6px;
                margin: 0;
            }
            QScrollBar::handle:horizontal {
                background-color: #00ff88;
                border-radius: 6px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #00cc6a;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
                background: none;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: #2d2d2d;
            }
            QPushButton#secondaryBtn {
                background-color: #3d3d3d;
                color: white;
                border: 2px solid #00ff88;
            }
            QPushButton#secondaryBtn:hover {
                background-color: #4d4d4d;
                border: 2px solid #00cc6a;
            }
        """)

    def setup_ui(self):
        """Setup main UI with tabs"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)

        # Create tabs
        self.search_tab = self.create_search_tab()
        self.downloads_tab = self.create_downloads_tab()
        self.settings_tab = self.create_settings_tab()
        self.about_tab = self.create_about_tab()

        self.tab_widget.addTab(self.search_tab, self.get_text('tab_search'))
        self.tab_widget.addTab(self.downloads_tab, self.get_text('tab_downloads'))
        self.tab_widget.addTab(self.settings_tab, self.get_text('tab_settings'))
        self.tab_widget.addTab(self.about_tab, self.get_text('tab_about'))

        main_layout.addWidget(self.tab_widget)

        # Footer
        footer = QLabel(self.get_text('footer'))
        footer.setStyleSheet("color: #555555; font-size: 11px;")
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)

    def create_search_tab(self) -> QWidget:
        """Create search tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Header with output folder
        header_layout = QHBoxLayout()

        title_label = QLabel(self.get_text('app_title'))
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #00ff88;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.output_btn = QPushButton(f"📁 {os.path.basename(self.output_path)}")
        self.output_btn.setObjectName("secondaryBtn")
        self.output_btn.clicked.connect(self.browse_folder)
        header_layout.addWidget(self.output_btn)

        layout.addLayout(header_layout)

        # Search box
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.get_text('search_placeholder'))
        self.search_input.returnPressed.connect(self.do_search)
        search_layout.addWidget(self.search_input, 1)

        self.search_btn = QPushButton(self.get_text('search_btn'))
        self.search_btn.clicked.connect(self.do_search)
        search_layout.addWidget(self.search_btn)

        layout.addLayout(search_layout)

        # Content splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left - Results
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 10, 0)

        results_label = QLabel(self.get_text('results'))
        results_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        left_layout.addWidget(results_label)

        self.results_list = QListWidget()
        self.results_list.setMinimumWidth(450)
        self.results_list.itemClicked.connect(self.on_video_selected)
        left_layout.addWidget(self.results_list)

        splitter.addWidget(left_widget)

        # Right - Preview and options
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)

        # Preview
        preview_group = QGroupBox(self.get_text('preview'))
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(8)

        # Title ABOVE video
        self.preview_title = QLabel(self.get_text('no_video_selected'))
        self.preview_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ff88;")
        self.preview_title.setWordWrap(True)
        self.preview_title.setAlignment(Qt.AlignCenter)
        self.preview_title.setMaximumHeight(40)
        preview_layout.addWidget(self.preview_title)

        # Meta (channel/time) ABOVE video
        self.preview_meta = QLabel("")
        self.preview_meta.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        self.preview_meta.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.preview_meta)

        # Thumbnail
        self.preview_thumbnail = QLabel()
        self.preview_thumbnail.setFixedSize(320, 180)
        self.preview_thumbnail.setStyleSheet("background-color: #2d2d2d; border-radius: 8px;")
        self.preview_thumbnail.setAlignment(Qt.AlignCenter)
        self.preview_thumbnail.setText(f"🎬\n\n{self.get_text('select_video')}")
        preview_layout.addWidget(self.preview_thumbnail, alignment=Qt.AlignCenter)

        # === PREVIEW PLAYER CONTROLS ===
        # Seek bar with time - BELOW thumbnail
        preview_seek_layout = QHBoxLayout()
        preview_seek_layout.setSpacing(8)

        self.preview_time_current = QLabel("0:00")
        self.preview_time_current.setStyleSheet("color: #00ff88; font-size: 11px; min-width: 35px;")
        preview_seek_layout.addWidget(self.preview_time_current)

        self.preview_seek_slider = ClickableSlider(Qt.Horizontal)
        self.preview_seek_slider.setRange(0, 100)
        self.preview_seek_slider.setMinimumHeight(20)
        self.preview_seek_slider.sliderMoved.connect(self.preview_seek_position)
        self.preview_seek_slider.sliderPressed.connect(lambda: setattr(self, 'preview_slider_pressed_flag', True))
        self.preview_seek_slider.sliderReleased.connect(self.preview_slider_released)
        preview_seek_layout.addWidget(self.preview_seek_slider, 1)

        self.preview_time_total = QLabel("0:00")
        self.preview_time_total.setStyleSheet("color: #888888; font-size: 11px; min-width: 35px;")
        preview_seek_layout.addWidget(self.preview_time_total)
        preview_layout.addLayout(preview_seek_layout)

        # Play button CENTERED, Volume on RIGHT
        preview_controls_layout = QHBoxLayout()

        # Spacer left (same width as volume to center play button)
        left_spacer = QWidget()
        left_spacer.setFixedWidth(120)
        preview_controls_layout.addWidget(left_spacer)

        preview_controls_layout.addStretch()

        # Play button centered
        self.preview_play_btn = QPushButton("▶ Play")
        self.preview_play_btn.setFixedSize(110, 40)
        self.preview_play_btn.clicked.connect(self.toggle_preview_play)
        self.preview_play_btn.setEnabled(False)
        self.preview_is_playing = False
        preview_controls_layout.addWidget(self.preview_play_btn)

        # Add some bottom margin to prevent clipping
        preview_controls_layout.setContentsMargins(0, 5, 0, 8)

        preview_controls_layout.addStretch()

        # Volume right side
        self.preview_volume_label = QLabel("70%")
        self.preview_volume_label.setStyleSheet("color: #888888; font-size: 11px; min-width: 35px;")
        preview_controls_layout.addWidget(self.preview_volume_label)

        self.preview_volume_slider = QSlider(Qt.Horizontal)
        self.preview_volume_slider.setRange(0, 100)
        self.preview_volume_slider.setValue(70)
        self.preview_volume_slider.setFixedWidth(80)
        self.preview_volume_slider.setMinimumHeight(20)
        self.preview_volume_slider.valueChanged.connect(self.change_preview_volume)
        preview_controls_layout.addWidget(self.preview_volume_slider)

        preview_layout.addLayout(preview_controls_layout)
        # === END PREVIEW CONTROLS ===

        right_layout.addWidget(preview_group)

        # Format
        format_group = QGroupBox(self.get_text('format'))
        format_layout = QVBoxLayout(format_group)

        type_layout = QHBoxLayout()
        self.type_group = QButtonGroup()

        self.video_radio = QRadioButton(self.get_text('video'))
        self.video_radio.setChecked(True)
        self.video_radio.toggled.connect(self.update_quality_options)
        self.type_group.addButton(self.video_radio)
        type_layout.addWidget(self.video_radio)

        self.audio_radio = QRadioButton(self.get_text('audio'))
        self.audio_radio.toggled.connect(self.update_quality_options)
        self.type_group.addButton(self.audio_radio)
        type_layout.addWidget(self.audio_radio)
        type_layout.addStretch()
        format_layout.addLayout(type_layout)

        quality_layout = QHBoxLayout()
        quality_label = QLabel(self.get_text('quality'))
        quality_layout.addWidget(quality_label)

        self.quality_combo = QComboBox()
        self.update_quality_options()
        quality_layout.addWidget(self.quality_combo, 1)
        format_layout.addLayout(quality_layout)

        right_layout.addWidget(format_group)

        # Status
        status_group = QGroupBox(self.get_text('status'))
        status_layout = QVBoxLayout(status_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        status_layout.addWidget(self.progress_bar)

        self.status_label = QLabel(self.get_text('waiting'))
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)

        right_layout.addWidget(status_group)

        # Download button
        self.download_btn = QPushButton(self.get_text('download_btn'))
        self.download_btn.setObjectName("downloadBtn")
        self.download_btn.setMinimumHeight(60)
        self.download_btn.clicked.connect(self.do_download)
        self.download_btn.setEnabled(False)
        right_layout.addWidget(self.download_btn)

        right_layout.addStretch()

        splitter.addWidget(right_widget)
        splitter.setSizes([550, 400])

        layout.addWidget(splitter, 1)

        return tab

    def create_downloads_tab(self) -> QWidget:
        """Create downloads tab with player"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title and buttons
        header_layout = QHBoxLayout()

        title = QLabel(self.get_text('downloads_title'))
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00ff88;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.clear_btn = QPushButton(self.get_text('clear_completed'))
        self.clear_btn.setObjectName("secondaryBtn")
        self.clear_btn.clicked.connect(self.clear_completed_downloads)
        header_layout.addWidget(self.clear_btn)

        self.open_folder_btn = QPushButton(self.get_text('open_folder'))
        self.open_folder_btn.setObjectName("secondaryBtn")
        self.open_folder_btn.clicked.connect(self.open_downloads_folder)
        header_layout.addWidget(self.open_folder_btn)

        layout.addLayout(header_layout)

        # Downloads table
        self.downloads_table = QTableWidget()
        self.downloads_table.setColumnCount(4)
        self.downloads_table.setHorizontalHeaderLabels([
            self.get_text('filename'),
            self.get_text('progress'),
            self.get_text('status_col'),
            self.get_text('actions')
        ])
        self.downloads_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.downloads_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.downloads_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.downloads_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.downloads_table.setColumnWidth(1, 200)
        self.downloads_table.setColumnWidth(2, 80)
        self.downloads_table.setColumnWidth(3, 120)
        self.downloads_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.downloads_table.verticalHeader().setVisible(False)

        # Placeholder
        self.downloads_placeholder = QLabel(self.get_text('no_downloads'))
        self.downloads_placeholder.setAlignment(Qt.AlignCenter)
        self.downloads_placeholder.setStyleSheet("color: #666666; font-size: 14px;")

        layout.addWidget(self.downloads_placeholder)
        layout.addWidget(self.downloads_table)
        self.downloads_table.hide()

        # Media player section
        player_group = QGroupBox(self.get_text('player_title'))
        player_layout = QVBoxLayout(player_group)

        # Now playing
        self.now_playing_label = QLabel(f"{self.get_text('now_playing')} {self.get_text('nothing_playing')}")
        self.now_playing_label.setStyleSheet("font-size: 13px; color: #aaaaaa;")
        self.now_playing_label.setAlignment(Qt.AlignCenter)
        player_layout.addWidget(self.now_playing_label)

        # Seek slider
        seek_layout = QHBoxLayout()

        self.time_current = QLabel("0:00")
        self.time_current.setStyleSheet("color: #888888; font-size: 12px;")
        seek_layout.addWidget(self.time_current)

        self.seek_slider = ClickableSlider(Qt.Horizontal)
        self.seek_slider.setRange(0, 100)
        self.seek_slider.sliderMoved.connect(self.seek_position)
        self.seek_slider.sliderPressed.connect(self.slider_pressed)
        self.seek_slider.sliderReleased.connect(self.slider_released)
        seek_layout.addWidget(self.seek_slider, 1)

        self.time_total = QLabel("0:00")
        self.time_total.setStyleSheet("color: #888888; font-size: 12px;")
        seek_layout.addWidget(self.time_total)

        player_layout.addLayout(seek_layout)

        # Volume control only (play/stop is in table Actions)
        volume_layout = QHBoxLayout()
        volume_layout.addStretch()

        self.volume_label = QLabel("70%")
        self.volume_label.setStyleSheet("color: #888888; font-size: 11px; min-width: 35px;")
        volume_layout.addWidget(self.volume_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(self.volume_slider)

        player_layout.addLayout(volume_layout)

        layout.addWidget(player_group)

        # Timer for position update
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self.update_position)
        self.slider_is_pressed = False

        # Media player signals
        self.media_player.positionChanged.connect(self.on_position_changed)
        self.media_player.durationChanged.connect(self.on_duration_changed)
        self.media_player.playbackStateChanged.connect(self.on_playback_state_changed)

        # Set initial volume
        self.audio_output.setVolume(0.7)

        return tab

    def create_settings_tab(self) -> QWidget:
        """Create settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel(self.get_text('settings_title'))
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #00ff88;")
        layout.addWidget(title)

        # Language
        lang_group = QGroupBox(self.get_text('language'))
        lang_layout = QHBoxLayout(lang_group)

        self.language_combo = QComboBox()
        self.language_combo.addItem("🇬🇧 English", "en")
        self.language_combo.addItem("🇩🇪 Deutsch", "de")
        self.language_combo.addItem("🇭🇷🇷🇸 Hrvatski/Srpski", "hr")

        # Set current
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == self.current_language:
                self.language_combo.setCurrentIndex(i)
                break

        lang_layout.addWidget(self.language_combo)
        lang_layout.addStretch()
        layout.addWidget(lang_group)

        # Appearance
        appearance_group = QGroupBox(self.get_text('appearance'))
        appearance_layout = QVBoxLayout(appearance_group)

        self.tray_checkbox = QCheckBox(self.get_text('system_tray'))
        self.tray_checkbox.setChecked(self.settings.value("show_tray", True, type=bool))
        appearance_layout.addWidget(self.tray_checkbox)

        self.minimize_tray_checkbox = QCheckBox(self.get_text('minimize_tray'))
        self.minimize_tray_checkbox.setChecked(self.settings.value("minimize_to_tray", False, type=bool))
        appearance_layout.addWidget(self.minimize_tray_checkbox)

        self.start_minimized_checkbox = QCheckBox(self.get_text('start_minimized'))
        self.start_minimized_checkbox.setChecked(self.settings.value("start_minimized", False, type=bool))
        appearance_layout.addWidget(self.start_minimized_checkbox)

        self.notifications_checkbox = QCheckBox(self.get_text('notifications'))
        self.notifications_checkbox.setChecked(self.settings.value("notifications", True, type=bool))
        appearance_layout.addWidget(self.notifications_checkbox)

        layout.addWidget(appearance_group)

        # Downloads settings
        downloads_group = QGroupBox(self.get_text('downloads_settings'))
        downloads_layout = QVBoxLayout(downloads_group)

        simultaneous_layout = QHBoxLayout()
        simultaneous_label = QLabel(self.get_text('simultaneous'))
        simultaneous_layout.addWidget(simultaneous_label)

        self.simultaneous_spin = QSpinBox()
        self.simultaneous_spin.setRange(1, 5)
        self.simultaneous_spin.setValue(self.settings.value("simultaneous_downloads", 2, type=int))
        simultaneous_layout.addWidget(self.simultaneous_spin)
        simultaneous_layout.addStretch()
        downloads_layout.addLayout(simultaneous_layout)

        self.auto_play_checkbox = QCheckBox(self.get_text('auto_play'))
        self.auto_play_checkbox.setChecked(self.settings.value("auto_play", False, type=bool))
        downloads_layout.addWidget(self.auto_play_checkbox)

        layout.addWidget(downloads_group)

        # Playback settings
        playback_group = QGroupBox("Playback")
        playback_layout = QVBoxLayout(playback_group)

        config = self.load_app_config()

        # Video player settings (audio uses built-in PySide6 player)
        video_header = QLabel("Video Files:")
        video_header.setStyleSheet("font-weight: bold; color: #00aaff;")
        playback_layout.addWidget(video_header)

        video_player_layout = QHBoxLayout()
        video_player_layout.addWidget(QLabel("Player:"))

        current_video_player = config.get('video_player', '')
        self.video_player_label = QLabel(current_video_player if current_video_player else "Always ask (default)")
        self.video_player_label.setStyleSheet("color: #aaaaaa; min-width: 120px;")
        video_player_layout.addWidget(self.video_player_label)
        video_player_layout.addStretch()

        self.set_video_player_btn = QPushButton("Change...")
        self.set_video_player_btn.clicked.connect(self.configure_video_player)
        video_player_layout.addWidget(self.set_video_player_btn)

        self.reset_video_player_btn = QPushButton("Reset")
        self.reset_video_player_btn.clicked.connect(self.reset_video_player)
        video_player_layout.addWidget(self.reset_video_player_btn)

        playback_layout.addLayout(video_player_layout)

        layout.addWidget(playback_group)

        layout.addStretch()

        # Save button
        save_btn = QPushButton(self.get_text('save_settings'))
        save_btn.clicked.connect(self.save_settings)
        save_btn.setMaximumWidth(250)
        layout.addWidget(save_btn, alignment=Qt.AlignCenter)

        return tab

    def create_about_tab(self) -> QWidget:
        """Create about tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        # About text - expands to fill space
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml(self.get_text('about_description', version=APP_VERSION))
        layout.addWidget(about_text, 1)  # stretch factor 1 = expand

        # Buttons at bottom
        links_layout = QHBoxLayout()
        links_layout.addStretch()

        github_btn = QPushButton(self.get_text('github'))
        github_btn.setObjectName("secondaryBtn")
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/NeleBiH/BalkTube-Grabber-Pro/")))
        links_layout.addWidget(github_btn)

        bug_btn = QPushButton(self.get_text('report_bug'))
        bug_btn.setObjectName("secondaryBtn")
        bug_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/NeleBiH/BalkTube-Grabber-Pro/issues")))
        links_layout.addWidget(bug_btn)

        license_btn = QPushButton(self.get_text('license_title'))
        license_btn.setObjectName("secondaryBtn")
        license_btn.clicked.connect(self.show_license_dialog)
        links_layout.addWidget(license_btn)

        links_layout.addStretch()
        layout.addLayout(links_layout)

        return tab

    def show_license_dialog(self):
        """Show license in a popup dialog"""
        from PySide6.QtWidgets import QDialog, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle(self.get_text('license_title'))
        dialog.setMinimumSize(500, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
            }
            QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton {
                background-color: #00ff88;
                color: #1a1a1a;
                font-weight: bold;
                padding: 8px 20px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #00cc6a;
            }
        """)

        layout = QVBoxLayout(dialog)

        license_text = QTextEdit()
        license_text.setReadOnly(True)
        license_text.setHtml(self.tr.get('license_text', TRANSLATIONS['en']['license_text']))
        layout.addWidget(license_text)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        dialog.exec()

    def setup_system_tray(self):
        """Setup system tray icon"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self)

            # Load icon from file or use fallback
            icon_path = os.path.join(APP_DIR, "Icons", "icon_64x64.png")
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
            else:
                pixmap = QPixmap(32, 32)
                pixmap.fill(QColor("#00ff88"))
                self.tray_icon.setIcon(QIcon(pixmap))

            # Menu
            tray_menu = QMenu()

            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)

            tray_menu.addSeparator()

            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(QApplication.quit)
            tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_activated)

            if self.settings.value("show_tray", True, type=bool):
                self.tray_icon.show()

    def tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()

    def changeEvent(self, event):
        """Handle window state changes"""
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized() and self.settings.value("minimize_to_tray", False, type=bool):
                event.ignore()
                self.hide()
                if self.tray_icon:
                    self.tray_icon.showMessage(
                        APP_NAME,
                        "Application minimized to tray",
                        QSystemTrayIcon.Information,
                        2000
                    )
        super().changeEvent(event)

    def connect_signals(self):
        """Connect worker signals"""
        self.signals.search_results.connect(self.on_search_results)
        self.signals.thumbnail_ready.connect(self.on_thumbnail_ready)
        self.signals.progress.connect(self.on_download_progress)
        self.signals.finished.connect(self.on_download_finished)
        self.signals.error.connect(self.on_download_error)

        # Preview player signals
        self.preview_player.positionChanged.connect(self.on_preview_position_changed)
        self.preview_player.durationChanged.connect(self.on_preview_duration_changed)
        self.preview_player.playbackStateChanged.connect(self.on_preview_state_changed)

    def load_settings(self):
        """Load saved settings"""
        pass  # Already loaded in __init__

    def save_settings(self):
        """Save settings"""
        new_lang = self.language_combo.currentData()

        self.settings.setValue("language", new_lang)
        self.settings.setValue("show_tray", self.tray_checkbox.isChecked())
        self.settings.setValue("minimize_to_tray", self.minimize_tray_checkbox.isChecked())
        self.settings.setValue("start_minimized", self.start_minimized_checkbox.isChecked())
        self.settings.setValue("notifications", self.notifications_checkbox.isChecked())
        self.settings.setValue("simultaneous_downloads", self.simultaneous_spin.value())
        self.settings.setValue("auto_play", self.auto_play_checkbox.isChecked())
        self.settings.setValue("output_path", self.output_path)

        # Update tray visibility
        if self.tray_icon:
            self.tray_icon.setVisible(self.tray_checkbox.isChecked())

        # Show message
        if new_lang != self.current_language:
            QMessageBox.information(
                self,
                "Language Changed",
                "Please restart the application to apply language changes."
            )
        else:
            self.status_label.setText(self.get_text('settings_saved'))

        log.info("Settings saved")

    def load_downloads(self):
        """Load downloads history from JSON file"""
        try:
            if os.path.exists(self.downloads_file):
                with open(self.downloads_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item_data in data:
                        # Only load completed or error downloads (skip in-progress)
                        if item_data.get('status') in ('done', 'error'):
                            item = DownloadItem.from_dict(item_data)
                            self.downloads[item.id] = item
                            self.add_download_to_table(item, from_history=True)
                log.info(f"Loaded {len(self.downloads)} downloads from history")
        except Exception as e:
            log.error(f"Failed to load downloads: {e}")

    def save_downloads(self):
        """Save downloads history to JSON file"""
        try:
            # Only save completed or error downloads
            data = [
                d.to_dict() for d in self.downloads.values()
                if d.status in ('done', 'error')
            ]
            with open(self.downloads_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            log.info(f"Saved {len(data)} downloads to history")
        except Exception as e:
            log.error(f"Failed to save downloads: {e}")

    def browse_folder(self):
        """Browse for output folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", self.output_path)
        if folder:
            self.output_path = folder
            self.output_btn.setText(f"📁 {os.path.basename(folder)}")

    def configure_video_player(self):
        """Configure default video player"""
        player = self.select_external_player("video")
        if player:
            config = self.load_app_config()
            config['video_player'] = player
            self.save_app_config(config)
            self.video_player_label.setText(player)
            log.info(f"Video player set to: {player}")

    def reset_video_player(self):
        """Reset to always ask for video player"""
        config = self.load_app_config()
        config['video_player'] = ''
        self.save_app_config(config)
        self.video_player_label.setText("Always ask (default)")
        log.info("Video player reset to always ask")

    def update_quality_options(self):
        """Update quality options based on format type"""
        self.quality_combo.clear()

        if self.video_radio.isChecked():
            options = [
                self.get_text('best_quality'),
                "2160p (4K)",
                "1440p (2K)",
                "1080p (Full HD)",
                "720p (HD)",
                "480p",
                "360p",
                "240p",
            ]
        else:
            options = [
                "MP3 - 320kbps",
                "MP3 - 256kbps",
                "MP3 - 192kbps",
                "MP3 - 128kbps",
                "AAC - 256kbps",
                "AAC - 192kbps",
                "FLAC (lossless)",
                "WAV (lossless)",
                "OGG - 320kbps",
                "OGG - 192kbps",
            ]

        self.quality_combo.addItems(options)

    def do_search(self):
        """Start search"""
        query = self.search_input.text().strip()
        log.info(f"🔍 Search: '{query}'")

        if not query:
            QMessageBox.warning(self, "Empty Search", "Please enter something to search!")
            return

        if 'youtube.com' in query or 'youtu.be' in query:
            self.set_direct_url(query)
            return

        self.search_btn.setEnabled(False)
        self.search_btn.setText(self.get_text('searching'))
        self.results_list.clear()
        self.status_label.setText(self.get_text('searching'))

        self.search_worker = SearchWorker(query, self.signals)
        self.search_worker.start()

    def set_direct_url(self, url: str):
        """Set direct URL as selected video"""
        self.selected_video = {'url': url, 'title': 'Loading...', 'thumbnail': ''}
        self.preview_title.setText("Loading video info...")
        self.download_btn.setEnabled(True)
        threading.Thread(target=self.fetch_video_info, args=(url,), daemon=True).start()

    def fetch_video_info(self, url: str):
        """Fetch video info from URL"""
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)

            self.selected_video = {
                'url': url,
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'channel': info.get('channel', 'Unknown'),
            }

            QMetaObject.invokeMethod(self, "_update_preview_info", Qt.QueuedConnection)

            if self.selected_video.get('thumbnail'):
                self.load_preview_thumbnail(self.selected_video['thumbnail'])

        except Exception as e:
            log.error(f"Error fetching video info: {e}")

    @Slot()
    def _update_preview_info(self):
        """Update preview info from main thread"""
        if self.selected_video:
            self.preview_title.setText(self.selected_video.get('title', 'Unknown'))
            duration = self.selected_video.get('duration', 0)
            if duration:
                duration = int(duration)
                duration_str = f"{duration // 60}:{duration % 60:02d}"
            else:
                duration_str = "N/A"
            self.preview_meta.setText(f"📺 {self.selected_video.get('channel', '')} | ⏱️ {duration_str}")

    def load_preview_thumbnail(self, url: str):
        """Load preview thumbnail"""
        def fetch():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self._preview_data = response.content
                    QMetaObject.invokeMethod(self, "_set_preview_pixmap", Qt.QueuedConnection)
            except Exception as e:
                log.error(f"Preview thumbnail error: {e}")

        threading.Thread(target=fetch, daemon=True).start()

    @Slot()
    def _set_preview_pixmap(self):
        """Set preview pixmap from main thread"""
        if hasattr(self, '_preview_data') and self._preview_data:
            pixmap = QPixmap()
            if pixmap.loadFromData(self._preview_data):
                scaled = pixmap.scaled(320, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.preview_thumbnail.setPixmap(scaled)
            self._preview_data = None

    @Slot(list)
    def on_search_results(self, videos: List[Dict]):
        """Handle search results"""
        log.info(f"📋 Received {len(videos)} results")

        self.search_btn.setEnabled(True)
        self.search_btn.setText(self.get_text('search_btn'))
        self.current_videos = videos
        self.thumbnail_workers.clear()

        if not videos:
            self.status_label.setText(self.get_text('no_results'))
            return

        self.status_label.setText(self.get_text('found_videos', count=len(videos)))

        for i, video in enumerate(videos):
            item = QListWidgetItem()
            widget = VideoItemWidget(video)
            item.setSizeHint(QSize(self.results_list.width() - 30, 110))
            item.setData(Qt.UserRole, i)
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, widget)

            if video.get('thumbnail'):
                worker = ThumbnailWorker(i, video['thumbnail'], self.signals)
                self.thumbnail_workers.append(worker)
                worker.start()

    @Slot(int, QPixmap)
    def on_thumbnail_ready(self, index: int, pixmap: QPixmap):
        """Handle thumbnail ready"""
        if index < self.results_list.count():
            item = self.results_list.item(index)
            widget = self.results_list.itemWidget(item)
            if widget and isinstance(widget, VideoItemWidget):
                widget.set_thumbnail(pixmap)

    def on_video_selected(self, item: QListWidgetItem):
        """Handle video selection"""
        index = item.data(Qt.UserRole)
        if index is not None and index < len(self.current_videos):
            self.selected_video = self.current_videos[index]

            self.preview_title.setText(self.selected_video.get('title', 'Unknown'))

            duration = self.selected_video.get('duration', 0)
            if duration:
                duration = int(duration)
                duration_str = f"{duration // 60}:{duration % 60:02d}"
            else:
                duration_str = "N/A"

            self.preview_meta.setText(f"📺 {self.selected_video.get('channel', '')} | ⏱️ {duration_str}")

            if self.selected_video.get('thumbnail'):
                self.load_preview_thumbnail(self.selected_video['thumbnail'])

            self.download_btn.setEnabled(True)
            self.preview_play_btn.setEnabled(True)
            self.status_label.setText(self.get_text('ready_download'))
            self.stop_preview()  # Reset preview

    # ============ PREVIEW PLAYER METHODS ============
    def toggle_preview_play(self):
        """Toggle preview play/stop"""
        if self.preview_is_playing:
            self.stop_preview()
        else:
            self.start_preview_stream()

    def start_preview_stream(self):
        """Start streaming preview from YouTube"""
        if not self.selected_video:
            return

        url = self.selected_video.get('url')
        if not url:
            video_id = self.selected_video.get('id')
            if video_id:
                url = f"https://www.youtube.com/watch?v={video_id}"
            else:
                return

        self.preview_play_btn.setText("...")
        self.preview_play_btn.setEnabled(False)
        self.status_label.setText("Loading preview...")

        threading.Thread(target=self._fetch_stream_url, args=(url,), daemon=True).start()

    def _fetch_stream_url(self, url: str):
        """Fetch streaming URL from YouTube"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'allow_remote_components': 'ejs:github',
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                # Try to get direct URL or from formats
                stream_url = info.get('url')
                if not stream_url and info.get('formats'):
                    # Find best audio format with URL
                    for fmt in reversed(info['formats']):
                        if fmt.get('url') and fmt.get('acodec') and fmt.get('acodec') != 'none':
                            stream_url = fmt['url']
                            log.debug(f"Using format: {fmt.get('format_id')} - {fmt.get('acodec')}")
                            break
                    # Fallback to any format with URL
                    if not stream_url:
                        for fmt in reversed(info['formats']):
                            if fmt.get('url'):
                                stream_url = fmt['url']
                                log.debug(f"Fallback format: {fmt.get('format_id')}")
                                break
                if stream_url:
                    QMetaObject.invokeMethod(self, "_play_stream", Qt.QueuedConnection, Q_ARG(str, stream_url))
                else:
                    log.error("No stream URL found in formats")
                    QMetaObject.invokeMethod(self, "_preview_error", Qt.QueuedConnection)
        except Exception as e:
            log.error(f"Preview error: {e}")
            QMetaObject.invokeMethod(self, "_preview_error", Qt.QueuedConnection)

    @Slot(str)
    def _play_stream(self, stream_url: str):
        """Play stream URL"""
        self.preview_player.setSource(QUrl(stream_url))
        self.preview_player.play()
        self.preview_is_playing = True
        self.preview_play_btn.setText("⏹ Stop")
        self.preview_play_btn.setEnabled(True)
        self.status_label.setText("Playing preview...")

    @Slot()
    def _preview_error(self):
        """Handle preview error"""
        self.preview_is_playing = False
        self._set_preview_btn_play()
        self.preview_play_btn.setEnabled(True)
        self.status_label.setText("Preview failed ❌")

    def stop_preview(self):
        """Stop preview"""
        self.preview_player.stop()
        self.preview_is_playing = False
        self._set_preview_btn_play()
        self.preview_seek_slider.setValue(0)
        self.preview_time_current.setText("0:00")
        if self.selected_video:
            self.status_label.setText(self.get_text('ready_download'))

    def _set_preview_btn_play(self):
        """Set preview button to play"""
        self.preview_play_btn.setText("▶ Play")

    def preview_seek_position(self, position):
        """Seek preview"""
        if self.preview_player.duration() > 0:
            self.preview_player.setPosition(int(position * self.preview_player.duration() / 100))

    def preview_slider_released(self):
        """Handle slider release"""
        self.preview_slider_pressed_flag = False
        self.preview_seek_position(self.preview_seek_slider.value())

    def change_preview_volume(self, value):
        """Change preview volume"""
        self.preview_audio_output.setVolume(value / 100.0)
        self.preview_volume_label.setText(f"{value}%")

    def on_preview_position_changed(self, position):
        """Handle preview position"""
        if not self.preview_slider_pressed_flag and self.preview_player.duration() > 0:
            self.preview_seek_slider.setValue(int(position * 100 / self.preview_player.duration()))
        secs = position // 1000
        self.preview_time_current.setText(f"{secs // 60}:{secs % 60:02d}")

    def on_preview_duration_changed(self, duration):
        """Handle preview duration"""
        secs = duration // 1000
        self.preview_time_total.setText(f"{secs // 60}:{secs % 60:02d}")

    def on_preview_state_changed(self, state):
        """Handle preview state"""
        if state == QMediaPlayer.StoppedState:
            self.preview_is_playing = False
            self._set_preview_btn_play()

    def do_download(self):
        """Start download"""
        if not self.selected_video:
            return

        url = self.selected_video.get('url')
        if not url:
            video_id = self.selected_video.get('id')
            if video_id:
                url = f"https://www.youtube.com/watch?v={video_id}"
            else:
                return

        # Create download item
        format_type = 'audio' if self.audio_radio.isChecked() else 'video'
        quality = self.quality_combo.currentText()

        download = DownloadItem(
            url=url,
            title=self.selected_video.get('title', 'Unknown'),
            output_path=self.output_path,
            format_type=format_type,
            quality=quality
        )

        self.downloads[download.id] = download

        # Add to table
        self.add_download_to_table(download)

        # Start worker
        worker = DownloadWorker(download, self.signals)
        self.download_workers[download.id] = worker
        worker.start()

        # Update UI
        self.download_btn.setEnabled(False)
        self.status_label.setText(self.get_text('downloading', percent=0))

        # Switch to downloads tab
        self.tab_widget.setCurrentIndex(1)

        log.info(f"⬇️ Started download: {download.title}")

    def add_download_to_table(self, download: DownloadItem, from_history: bool = False):
        """Add download to table"""
        self.downloads_placeholder.hide()
        self.downloads_table.show()

        row = self.downloads_table.rowCount()
        self.downloads_table.insertRow(row)

        # Filename
        title_item = QTableWidgetItem(download.title[:50] + "..." if len(download.title) > 50 else download.title)
        title_item.setData(Qt.UserRole, download.id)
        title_item.setData(Qt.UserRole + 1, download.format_type)  # Store format type
        self.downloads_table.setItem(row, 0, title_item)

        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setTextVisible(True)
        self.downloads_table.setCellWidget(row, 1, progress_bar)

        # Status - text label
        status_item = QTableWidgetItem()
        status_item.setTextAlignment(Qt.AlignCenter)
        self.downloads_table.setItem(row, 2, status_item)

        # Play/Stop button
        play_btn = QPushButton("▶ Play")
        play_btn.setProperty("download_id", download.id)
        play_btn.setProperty("is_playing", False)
        play_btn.clicked.connect(lambda checked, d=download, btn=play_btn: self.toggle_download_play(d.id, btn))
        self.downloads_table.setCellWidget(row, 3, play_btn)

        # Set initial state based on whether loading from history
        if from_history:
            progress_bar.setValue(100)
            if download.status == 'done':
                if download.format_type == 'audio':
                    status_item.setText("Audio")
                    status_item.setForeground(QColor("#00ff88"))
                else:
                    status_item.setText("Video")
                    status_item.setForeground(QColor("#00aaff"))
                # Check if file still exists
                play_btn.setEnabled(download.filepath and os.path.exists(download.filepath))
            elif download.status == 'error':
                status_item.setText("Failed")
                status_item.setForeground(QColor("#ff4444"))
                play_btn.setEnabled(False)
        else:
            progress_bar.setValue(0)
            status_item.setText("Waiting...")
            status_item.setForeground(QColor("#888888"))
            play_btn.setEnabled(False)

        self.downloads_table.setRowHeight(row, 55)

    @Slot(str, float, str)
    def on_download_progress(self, download_id: str, percent: float, status: str):
        """Handle download progress"""
        if download_id in self.downloads:
            self.downloads[download_id].progress = percent
            self.downloads[download_id].status = status

            # Update table
            for row in range(self.downloads_table.rowCount()):
                item = self.downloads_table.item(row, 0)
                if item and item.data(Qt.UserRole) == download_id:
                    progress_bar = self.downloads_table.cellWidget(row, 1)
                    if progress_bar:
                        progress_bar.setValue(int(percent))

                    status_item = self.downloads_table.item(row, 2)
                    if status_item:
                        if status == "downloading":
                            status_item.setText("Downloading...")
                            status_item.setForeground(QColor("#00ff88"))
                        elif status == "processing":
                            status_item.setText("Processing...")
                            status_item.setForeground(QColor("#ffaa00"))
                    break

            # Update main progress bar
            self.progress_bar.setValue(int(percent))
            self.status_label.setText(self.get_text('downloading', percent=percent))

    @Slot(str, str, str)
    def on_download_finished(self, download_id: str, status: str, filepath: str):
        """Handle download finished"""
        log.info(f"✅ Download finished: {download_id}")

        if download_id in self.downloads:
            self.downloads[download_id].status = "done"
            self.downloads[download_id].filepath = filepath

            # Update table
            for row in range(self.downloads_table.rowCount()):
                item = self.downloads_table.item(row, 0)
                if item and item.data(Qt.UserRole) == download_id:
                    progress_bar = self.downloads_table.cellWidget(row, 1)
                    if progress_bar:
                        progress_bar.setValue(100)

                    status_item = self.downloads_table.item(row, 2)
                    if status_item:
                        # Get format type from title item
                        title_item = self.downloads_table.item(row, 0)
                        format_type = title_item.data(Qt.UserRole + 1) if title_item else "audio"
                        if format_type == "audio":
                            status_item.setText("Audio")
                            status_item.setForeground(QColor("#00ff88"))
                        else:
                            status_item.setText("Video")
                            status_item.setForeground(QColor("#00aaff"))

                    play_btn = self.downloads_table.cellWidget(row, 3)
                    if play_btn:
                        play_btn.setEnabled(True)
                    break

        # Re-enable download button
        self.download_btn.setEnabled(True)
        self.progress_bar.setValue(100)
        self.status_label.setText(self.get_text('done'))

        # Notification
        if self.settings.value("notifications", True, type=bool) and self.tray_icon:
            self.tray_icon.showMessage(
                "Download Complete",
                f"{self.downloads[download_id].title}",
                QSystemTrayIcon.Information,
                3000
            )

        # Auto-play
        if self.settings.value("auto_play", False, type=bool):
            self.play_downloaded(download_id)

        # Save downloads history
        self.save_downloads()

    @Slot(str, str)
    def on_download_error(self, download_id: str, error: str):
        """Handle download error"""
        log.error(f"❌ Download error: {error}")

        if download_id in self.downloads:
            self.downloads[download_id].status = "error"
            self.downloads[download_id].error_message = error

            for row in range(self.downloads_table.rowCount()):
                item = self.downloads_table.item(row, 0)
                if item and item.data(Qt.UserRole) == download_id:
                    status_item = self.downloads_table.item(row, 2)
                    if status_item:
                        status_item.setText("Failed")
                        status_item.setForeground(QColor("#ff4444"))
                    break

        self.download_btn.setEnabled(True)
        self.status_label.setText(self.get_text('error'))

        if 'ffmpeg' in error.lower():
            QMessageBox.critical(self, "FFmpeg Error",
                "FFmpeg is required for audio conversion.\n"
                "Please install FFmpeg and add it to PATH.")
        else:
            QMessageBox.critical(self, "Download Error", error)

        # Save downloads history
        self.save_downloads()

    def play_downloaded(self, download_id: str):
        """Play downloaded file"""
        if download_id in self.downloads:
            download = self.downloads[download_id]
            filepath = download.filepath

            if filepath and os.path.exists(filepath):
                log.info(f"▶️ Playing: {filepath}")

                self.media_player.setSource(QUrl.fromLocalFile(filepath))
                self.media_player.play()

                self.now_playing_label.setText(f"{self.get_text('now_playing')} {download.title}")
                self.player_is_playing = True
                self.position_timer.start(1000)
            else:
                log.warning(f"File not found: {filepath}")
                QMessageBox.warning(self, "File Not Found", f"Cannot find: {filepath}")

    def toggle_download_play(self, download_id: str, btn: QPushButton):
        """Toggle play/stop for a download item"""
        is_playing = btn.property("is_playing")

        if is_playing:
            # Stop playback
            self.stop_playback()
            btn.setText("▶ Play")
            btn.setProperty("is_playing", False)
            self.current_playing_download_id = None
            self.current_playing_btn = None
        else:
            # Stop any currently playing download first
            if self.current_playing_btn and self.current_playing_btn != btn:
                self.current_playing_btn.setText("▶ Play")
                self.current_playing_btn.setProperty("is_playing", False)
                self.stop_playback()

            # Start playback
            if download_id in self.downloads:
                download = self.downloads[download_id]
                filepath = download.filepath

                if filepath and os.path.exists(filepath):
                    # Check if video - use external player for video only
                    if download.format_type == 'video':
                        self.kill_external_player()
                        self.play_video_external(filepath, download.title)
                        btn.setText("⏹ Stop")
                        btn.setProperty("is_playing", True)
                        self.current_playing_download_id = download_id
                        self.current_playing_btn = btn
                    else:
                        # Audio - always use built-in PySide6 player
                        self.media_player.setSource(QUrl.fromLocalFile(filepath))
                        self.media_player.play()

                        self.now_playing_label.setText(f"{self.get_text('now_playing')} {download.title}")
                        self.player_is_playing = True
                        self.position_timer.start(1000)

                        btn.setText("⏹ Stop")
                        btn.setProperty("is_playing", True)
                        self.current_playing_download_id = download_id
                        self.current_playing_btn = btn
                else:
                    QMessageBox.warning(self, "File Not Found", f"Cannot find: {filepath}")

    def stop_playback(self):
        """Stop playback"""
        # Kill external player if running
        self.kill_external_player()

        # Stop built-in player
        self.media_player.stop()
        self.player_is_playing = False
        self.seek_slider.setValue(0)
        self.time_current.setText("0:00")
        self.position_timer.stop()
        self.now_playing_label.setText(f"{self.get_text('now_playing')} {self.get_text('nothing_playing')}")

        # Reset table button if playing from downloads
        if self.current_playing_btn:
            self.current_playing_btn.setText("▶ Play")
            self.current_playing_btn.setProperty("is_playing", False)
            self.current_playing_btn = None
            self.current_playing_download_id = None

    def play_video_external(self, filepath: str, title: str):
        """Play video in external player"""
        import subprocess

        # Load config
        config = self.load_app_config()
        video_player = config.get('video_player', '')

        # If no player configured, ask user
        if not video_player:
            video_player = self.select_external_player("video")
            if not video_player:
                return  # User cancelled

        # Kill previous external player if running
        self.kill_external_player()

        # Launch external player
        try:
            self.external_player_process = subprocess.Popen([video_player, filepath])
            log.info(f"▶️ Playing video in {video_player}: {title}")
            self.now_playing_label.setText(f"{self.get_text('now_playing')} {title}")
        except Exception as e:
            log.error(f"Failed to launch video player: {e}")
            QMessageBox.critical(self, "Error", f"Failed to launch video player:\n{e}")

    def kill_external_player(self):
        """Kill external player process if running"""
        if self.external_player_process:
            try:
                self.external_player_process.terminate()
                self.external_player_process.wait(timeout=1)
            except:
                try:
                    self.external_player_process.kill()
                except:
                    pass
            self.external_player_process = None
            log.info("Killed external player")

    def select_external_player(self, player_type: str = "video") -> str:
        """Show dialog to select external player"""
        import shutil

        # Find available players
        players = []
        player_commands = [
            ('VLC', 'vlc'),
            ('MPV', 'mpv'),
            ('Celluloid', 'celluloid'),
            ('Totem', 'totem'),
            ('Dragon Player', 'dragon'),
            ('SMPlayer', 'smplayer'),
            ('Parole', 'parole'),
            ('Audacious', 'audacious'),
            ('Clementine', 'clementine'),
            ('Rhythmbox', 'rhythmbox'),
            ('Elisa', 'elisa'),
        ]

        for name, cmd in player_commands:
            if shutil.which(cmd):
                players.append((name, cmd))

        if not players:
            QMessageBox.warning(self, f"No {player_type.title()} Player",
                f"No supported {player_type} player found.\nPlease install VLC, MPV, or another player.")
            return ''

        # Create selection dialog
        items = [f"{name} ({cmd})" for name, cmd in players]
        item, ok = QInputDialog.getItem(
            self,
            f"Select {player_type.title()} Player",
            f"Choose {player_type} player:",
            items,
            0,
            False
        )

        if ok and item:
            idx = items.index(item)
            return players[idx][1]
        return ''

    def load_app_config(self) -> dict:
        """Load app config from JSON"""
        config_file = os.path.expanduser("~/.config/BalkTube/config.json")
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            log.error(f"Failed to load config: {e}")
        return {}

    def save_app_config(self, config: dict):
        """Save app config to JSON"""
        config_file = os.path.expanduser("~/.config/BalkTube/config.json")
        try:
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            log.error(f"Failed to save config: {e}")

    def seek_position(self, position):
        """Seek to position"""
        if self.media_player.duration() > 0:
            new_pos = int(position * self.media_player.duration() / 100)
            self.media_player.setPosition(new_pos)

    def slider_pressed(self):
        """Handle slider pressed"""
        self.slider_is_pressed = True

    def slider_released(self):
        """Handle slider released"""
        self.slider_is_pressed = False
        self.seek_position(self.seek_slider.value())

    def change_volume(self, value):
        """Change volume"""
        self.audio_output.setVolume(value / 100.0)
        self.volume_label.setText(f"{value}%")

    def update_position(self):
        """Update position display"""
        pass  # Handled by signals now

    def on_position_changed(self, position):
        """Handle position change"""
        if not self.slider_is_pressed and self.media_player.duration() > 0:
            percent = int(position * 100 / self.media_player.duration())
            self.seek_slider.setValue(percent)

        # Update time label
        secs = position // 1000
        self.time_current.setText(f"{secs // 60}:{secs % 60:02d}")

    def on_duration_changed(self, duration):
        """Handle duration change"""
        secs = duration // 1000
        self.time_total.setText(f"{secs // 60}:{secs % 60:02d}")

    def on_playback_state_changed(self, state):
        """Handle playback state change"""
        if state == QMediaPlayer.StoppedState:
            self.player_is_playing = False
            self._set_player_btn_play()
            self.position_timer.stop()

    def _set_player_btn_play(self):
        """Reset the current playing button to Play state"""
        if self.current_playing_btn:
            self.current_playing_btn.setText("▶ Play")
            self.current_playing_btn.setProperty("is_playing", False)
            self.current_playing_btn = None
            self.current_playing_download_id = None

    def clear_completed_downloads(self):
        """Clear completed downloads from list"""
        rows_to_remove = []

        for row in range(self.downloads_table.rowCount()):
            item = self.downloads_table.item(row, 0)
            if item:
                download_id = item.data(Qt.UserRole)
                if download_id in self.downloads:
                    if self.downloads[download_id].status in ["done", "error"]:
                        rows_to_remove.append(row)
                        del self.downloads[download_id]

        for row in reversed(rows_to_remove):
            self.downloads_table.removeRow(row)

        if self.downloads_table.rowCount() == 0:
            self.downloads_table.hide()
            self.downloads_placeholder.show()

        log.info(f"Cleared {len(rows_to_remove)} completed downloads")

    def open_downloads_folder(self):
        """Open downloads folder"""
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_path))

    def closeEvent(self, event):
        """Handle close event"""
        if self.settings.value("minimize_to_tray", False, type=bool) and self.tray_icon and self.tray_icon.isVisible():
            # Stop music even when hiding to tray
            self.kill_external_player()
            self.media_player.stop()
            self.preview_player.stop()
            event.ignore()
            self.hide()
        else:
            # Kill external player (mpv/vlc) if running
            self.kill_external_player()

            # Stop all media players and release audio resources
            self.media_player.stop()
            self.preview_player.stop()
            self.position_timer.stop()

            # Disconnect audio outputs to stop sound
            self.media_player.setAudioOutput(None)
            self.preview_player.setAudioOutput(None)

            # Delete audio outputs
            self.audio_output.deleteLater()
            self.preview_audio_output.deleteLater()

            # Delete media players
            self.media_player.deleteLater()
            self.preview_player.deleteLater()

            # Save settings
            self.settings.setValue("output_path", self.output_path)

            # Hide tray icon
            if self.tray_icon:
                self.tray_icon.hide()

            event.accept()

            # Force quit application
            QApplication.quit()


# ============ MAIN ============
def main():
    log.info("=" * 50)
    log.info(f"🎵 {APP_NAME} v{APP_VERSION} - Starting...")
    log.info("=" * 50)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("BalkTube")

    # Set application icon
    icon_path = os.path.join(APP_DIR, "Icons", "icon_256x256.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = BalkTubeGrabber()

    # Check start minimized
    settings = QSettings("BalkTube", "GrabberPro")
    if settings.value("start_minimized", False, type=bool):
        window.hide()
    else:
        window.show()

    log.info("🚀 Application started!")
    log.info("-" * 50)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
