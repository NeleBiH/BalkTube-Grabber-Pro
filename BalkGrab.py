"""
🎵 BalkGrab v2.0 - ClipGrab clone done right! 🎵
- PySide6 GUI with tabs
- YouTube video search
- Download manager with progress tracking
- Integrated media player
- System tray support
- Multi-language (EN/DE/HR)

INSTALLATION:
pip install PySide6 yt-dlp requests

ALSO REQUIRED:
ffmpeg - for audio conversion
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
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QProgressBar,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QGroupBox, QRadioButton, QButtonGroup, QFrame, QSplitter,
    QStackedWidget, QSizePolicy, QScrollArea, QTabWidget,
    QSlider, QCheckBox, QTextEdit, QSystemTrayIcon, QMenu,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox, QInputDialog,
    QDialog, QToolButton
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
log = logging.getLogger("BalkGrab")

# ============ APP DIRECTORY ============
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = "windows" if sys.platform == "win32" else "linux"


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
APP_VERSION = "0.3.0"
APP_NAME = "BalkGrab"

# ============ TRANSLATIONS ============
TRANSLATIONS = {
    'en': {
        'app_title': '🎵 BalkGrab',
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
        'stop_download': '⏹  STOP DOWNLOAD  ⏹',
        'found_videos': 'Found {count} videos! 🎉',
        'load_more': '🔽 Load More Results',
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
        'ctx_play': 'Play',
        'ctx_open_folder': 'Open containing folder',
        'ctx_download_again': 'Download again',
        'ctx_convert_to': 'Convert to',
        'ctx_remove': 'Remove from list',
        'converting_file': 'Converting to {fmt}...',
        'conversion_done': 'Converted to {fmt}',
        'conversion_failed': 'Conversion failed: {error}',
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
        'continue_playing_tray': 'Continue playing when minimized to tray',
        'notifications': 'Show download notifications',
        'downloads_settings': 'Downloads',
        'simultaneous': 'Simultaneous downloads:',
        'auto_play': 'Auto-play after download',
        'download_location': 'Download location:',
        'save_settings': '💾 Save Settings',
        'settings_saved': 'Settings saved! ✅',
        # About
        'about_title': 'About BalkGrab',
        'about_description': '''
<h2>🎵 BalkGrab</h2>
<p><b>Version:</b> {version}</p>

<h3>What is this?</h3>
<p>BalkGrab is a free, open-source YouTube downloader inspired by ClipGrab.
Download videos in various resolutions or convert them to audio formats like MP3, FLAC, and more!</p>

<h3>Features</h3>
<ul>
<li>🔍 Search YouTube directly from the app</li>
<li>📺 Preview videos with built-in stream player</li>
<li>🎬 Download videos in resolutions from 240p to 4K</li>
<li>🎵 Convert to audio: MP3, AAC, FLAC, WAV, OGG</li>
<li>⬇️ Download manager with progress tracking</li>
<li>🎧 Built-in media player for downloaded files</li>
<li>📋 Smart playlist detection with batch download</li>
<li>📎 Clipboard auto-detection of YouTube URLs</li>
<li>🍪 Browser cookies support for age-restricted videos</li>
<li>🌍 Multi-language: English, Deutsch, Hrvatski/Srpski</li>
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
<p>Copyright (c) 2024-2026 BalkGrab Team</p>

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
        # Playlist
        'playlist_detected': 'Playlist Detected',
        'playlist_msg': 'This playlist contains {count} videos.\nWhat would you like to do?',
        'playlist_first_video': 'Show First Video',
        'playlist_load_first': 'First {count} videos',
        'playlist_load_all': 'All {count} videos',
        'playlist_load_btn': 'Load Playlist',
        'playlist_loading': 'Loading playlist info...',
        'playlist_warning': 'Loading many videos may be slow!',
        'playlist_cancel': 'Cancel',
        'footer': 'Made with ❤️,Claude code and some coffee | Balkan Edition 🇧🇦🇭🇷🇷🇸'
    },
    'de': {
        'app_title': '🎵 BalkGrab',
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
        'stop_download': '⏹  DOWNLOAD STOPPEN  ⏹',
        'found_videos': '{count} Videos gefunden! 🎉',
        'load_more': '🔽 Mehr Ergebnisse laden',
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
        'ctx_play': 'Abspielen',
        'ctx_open_folder': 'Ordner öffnen',
        'ctx_download_again': 'Erneut herunterladen',
        'ctx_convert_to': 'Konvertieren zu',
        'ctx_remove': 'Aus Liste entfernen',
        'converting_file': 'Konvertiere zu {fmt}...',
        'conversion_done': 'Zu {fmt} konvertiert',
        'conversion_failed': 'Konvertierung fehlgeschlagen: {error}',
        'player_title': '🎵 Mediaplayer',
        'now_playing': 'Wird abgespielt:',
        'nothing_playing': 'Nichts wird abgespielt',
        'settings_title': '⚙️ Einstellungen',
        'language': 'Sprache:',
        'appearance': 'Aussehen',
        'system_tray': 'Taskleistensymbol anzeigen',
        'minimize_tray': 'In Taskleiste minimieren',
        'start_minimized': 'Minimiert starten',
        'continue_playing_tray': 'Weiterspielen wenn in Taskleiste minimiert',
        'notifications': 'Download-Benachrichtigungen anzeigen',
        'downloads_settings': 'Downloads',
        'simultaneous': 'Gleichzeitige Downloads:',
        'auto_play': 'Nach Download automatisch abspielen',
        'download_location': 'Download-Speicherort:',
        'save_settings': '💾 Einstellungen speichern',
        'settings_saved': 'Einstellungen gespeichert! ✅',
        'about_title': 'Über BalkGrab',
        'about_description': '''
<h2>🎵 BalkGrab</h2>
<p><b>Version:</b> {version}</p>

<h3>Was ist das?</h3>
<p>BalkGrab ist ein kostenloser, Open-Source YouTube-Downloader inspiriert von ClipGrab.
Laden Sie Videos in verschiedenen Auflösungen herunter oder konvertieren Sie sie in Audioformate wie MP3, FLAC und mehr!</p>

<h3>Funktionen</h3>
<ul>
<li>🔍 YouTube direkt in der App durchsuchen</li>
<li>📺 Videos mit integriertem Stream-Player ansehen</li>
<li>🎬 Videos in Auflösungen von 240p bis 4K herunterladen</li>
<li>🎵 In Audio konvertieren: MP3, AAC, FLAC, WAV, OGG</li>
<li>⬇️ Download-Manager mit Fortschrittsverfolgung</li>
<li>🎧 Integrierter Mediaplayer für heruntergeladene Dateien</li>
<li>📋 Intelligente Playlist-Erkennung mit Batch-Download</li>
<li>📎 Automatische Erkennung von YouTube-URLs in der Zwischenablage</li>
<li>🍪 Browser-Cookies für altersbeschränkte Videos</li>
<li>🌍 Mehrsprachig: English, Deutsch, Hrvatski/Srpski</li>
<li>🖥️ Taskleisten-Integration</li>
</ul>
''',
        'license_title': '📜 Lizenz',
        'links_title': '🔗 Links',
        'github': '⭐ GitHub Repository',
        'report_bug': '🐛 Fehler melden',
        # Playlist
        'playlist_detected': 'Playlist erkannt',
        'playlist_msg': 'Diese Playlist enthält {count} Videos.\nWas möchten Sie tun?',
        'playlist_first_video': 'Erstes Video anzeigen',
        'playlist_load_first': 'Erste {count} Videos',
        'playlist_load_all': 'Alle {count} Videos',
        'playlist_load_btn': 'Playlist laden',
        'playlist_loading': 'Lade Playlist-Info...',
        'playlist_warning': 'Viele Videos zu laden kann langsam sein!',
        'playlist_cancel': 'Abbrechen',
        'footer': 'Mit ❤️ und etwas Ćevapi gemacht | Balkan Edition 🇧🇦🇭🇷🇷🇸'
    },
    'hr': {
        'app_title': '🎵 BalkGrab',
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
        'stop_download': '⏹  ZAUSTAVI SKIDANJE  ⏹',
        'found_videos': 'Pronađeno {count} videa! 🎉',
        'load_more': '🔽 Učitaj više rezultata',
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
        'ctx_play': 'Pusti',
        'ctx_open_folder': 'Otvori mapu',
        'ctx_download_again': 'Skini ponovo',
        'ctx_convert_to': 'Konvertuj u',
        'ctx_remove': 'Ukloni sa liste',
        'converting_file': 'Konvertuje se u {fmt}...',
        'conversion_done': 'Konvertovano u {fmt}',
        'conversion_failed': 'Konverzija neuspješna: {error}',
        'player_title': '🎵 Media Player',
        'now_playing': 'Sad svira:',
        'nothing_playing': 'Ništa ne svira',
        'settings_title': '⚙️ Postavke',
        'language': 'Jezik:',
        'appearance': 'Izgled',
        'system_tray': 'Prikaži ikonu u system trayu',
        'minimize_tray': 'Minimiziraj u system tray',
        'start_minimized': 'Pokreni minimizirano',
        'continue_playing_tray': 'Nastavi reprodukciju kad je minimizirano u tray',
        'notifications': 'Prikaži obavijesti o preuzimanju',
        'downloads_settings': 'Preuzimanja',
        'simultaneous': 'Istovremena preuzimanja:',
        'auto_play': 'Automatski pusti nakon preuzimanja',
        'download_location': 'Lokacija preuzimanja:',
        'save_settings': '💾 Spremi postavke',
        'settings_saved': 'Postavke spremljene! ✅',
        'about_title': 'O aplikaciji BalkGrab',
        'about_description': '''
<h2>🎵 BalkGrab</h2>
<p><b>Verzija:</b> {version}</p>

<h3>Šta je ovo?</h3>
<p>BalkGrab je besplatan YouTube downloader otvorenog koda inspiriran ClipGrab-om.
Skidaj videe u raznim rezolucijama ili ih pretvori u audio formate kao MP3, FLAC i druge!</p>

<h3>Mogućnosti</h3>
<ul>
<li>🔍 Pretraži YouTube direktno iz aplikacije</li>
<li>📺 Pregledaj video sa ugrađenim stream playerom</li>
<li>🎬 Skidaj videe u rezolucijama od 240p do 4K</li>
<li>🎵 Pretvori u audio: MP3, AAC, FLAC, WAV, OGG</li>
<li>⬇️ Upravitelj preuzimanja s praćenjem napretka</li>
<li>🎧 Ugrađeni media player za skinute fajlove</li>
<li>📋 Pametna detekcija playlisti sa batch downloadom</li>
<li>📎 Auto-detekcija YouTube linkova iz clipboarda</li>
<li>🍪 Browser cookies podrška za age-restricted videe</li>
<li>🌍 Višejezično: English, Deutsch, Hrvatski/Srpski</li>
<li>🖥️ System tray integracija</li>
</ul>
''',
        'license_title': '📜 Licenca',
        'license_text': '''
<h3>MIT Licenca</h3>
<p>Copyright (c) 2024-2026 BalkGrab Tim</p>

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
        # Playlist
        'playlist_detected': 'Playlist detektovan',
        'playlist_msg': 'Ova playlista sadrži {count} videa.\nŠta želiš uraditi?',
        'playlist_first_video': 'Prikaži prvi video',
        'playlist_load_first': 'Prvih {count} videa',
        'playlist_load_all': 'Svih {count} videa',
        'playlist_load_btn': 'Učitaj playlistu',
        'playlist_loading': 'Učitavam info o playlisti...',
        'playlist_warning': 'Učitavanje puno videa može biti sporo!',
        'playlist_cancel': 'Odustani',
        'footer': 'Napravljeno s ❤️ i malo kave | Balkan Edition 🇧🇦🇭🇷🇷🇸'
    }
}


# ============ WORKER SIGNALS ============
class WorkerSignals(QObject):
    """Signals for communication between worker threads and GUI"""
    progress = Signal(str, float, str)  # download_id, percentage, message
    finished = Signal(str, str, str)  # download_id, status, filepath
    error = Signal(str, str)  # download_id, error message
    search_results = Signal(list)  # list of search results
    thumbnail_ready = Signal(int, QPixmap)  # index, pixmap
    playlist_info = Signal(str, list)  # original_url, list of video dicts


# ============ DOWNLOAD ITEM ============
class DownloadItem:
    """Represents a single download"""
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
    """Search thread to keep GUI responsive"""

    def __init__(self, query: str, signals: WorkerSignals, count: int = 10):
        super().__init__()
        self.query = query
        self.signals = signals
        self.count = count

    def run(self):
        log.info(f"🔍 Starting search: '{self.query}' (count={self.count})")
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

                log.info(f"✅ Found {len(videos)} videos")
                self.signals.search_results.emit(videos)
            else:
                log.warning("⚠️ No results")
                self.signals.search_results.emit([])

        except Exception as e:
            log.error(f"❌ Search error: {str(e)}")
            self.signals.error.emit("search", f"Search error: {str(e)}")


# ============ THUMBNAIL WORKER ============
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
                log.debug(f"📷 Downloading thumbnail [{self.index}]")
                response = requests.get(self.url, timeout=10)
                if response.status_code == 200:
                    pixmap = QPixmap()
                    if pixmap.loadFromData(response.content):
                        self.signals.thumbnail_ready.emit(self.index, pixmap)
        except Exception as e:
            log.error(f"❌ Thumbnail [{self.index}] error: {e}")


# ============ DOWNLOAD WORKER ============
class DownloadWorker(QThread):
    """Thread for downloading video/audio"""

    def __init__(self, download_item: DownloadItem, signals: WorkerSignals, cookies_browser: str = ""):
        super().__init__()
        self.item = download_item
        self.signals = signals
        self.cookies_browser = cookies_browser
        self._cancelled = False

    def cancel(self):
        """Request cancellation of this download"""
        self._cancelled = True

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

            # Add cookies if configured
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
                    'remote_components': ['ejs:github'],
                    'noplaylist': True,
                    **cookies_opts,
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
                    'remote_components': ['ejs:github'],
                    'noplaylist': True,
                    **cookies_opts,
                }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.item.url, download=True)

                # Use yt-dlp's own filename to get the actual path on disk
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

        # Checkbox for multi-select
        self.checkbox = QCheckBox()
        self.checkbox.setStyleSheet("QCheckBox { spacing: 0px; } QCheckBox::indicator { width: 18px; height: 18px; }")
        layout.addWidget(self.checkbox)

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
class BalkGrabGrabber(QMainWindow):
    """Glavni prozor aplikacije"""

    def __init__(self):
        super().__init__()

        # Settings
        self.settings = QSettings("BalkGrab", "BalkGrab")
        self.current_language = self.settings.value("language", "en")
        self.tr = TRANSLATIONS[self.current_language]

        self.setWindowTitle(self.tr['app_title'])
        self.setMinimumSize(900, 650)
        self.resize(1100, 750)

        # Set window icon
        icon_path = os.path.join(APP_DIR, "Icons", ICON_DIR, "icon_256x256.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Downloads history file
        self.downloads_file = os.path.expanduser("~/.config/BalkGrab/downloads.json")
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
        self._active_download_id = None  # Track active download for stop button
        self._playlist_mode = False  # Track if current results are from playlist
        self._thumbnail_total = 0  # Total thumbnails to load
        self._thumbnail_loaded = 0  # Thumbnails loaded so far
        self._download_queue: List[str] = []  # Queue of pending batch download IDs
        self._active_batch_downloads: set = set()  # Currently running batch download IDs

        # Preview player for streaming
        self.preview_player = QMediaPlayer()
        self.preview_audio_output = QAudioOutput()
        self.preview_player.setAudioOutput(self.preview_audio_output)
        self.preview_audio_output.setVolume(0.7)
        self.preview_is_playing = False
        self.preview_slider_pressed_flag = False
        self._preview_auto_refreshing = False
        self._preview_stall_position = 0
        self._preview_last_position = -1
        self._preview_stall_count = 0

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

    def set_statusbar(self, message: str, error: bool = False):
        """Set status bar message with green (normal) or red (error) color"""
        color = "#ff4444" if error else "#00ff88"
        self.statusBar().setStyleSheet(
            f"QStatusBar {{ background: #1a1a2e; border-top: 1px solid #333; "
            f"font-size: 12px; color: {color}; }}"
        )
        self.statusBar().showMessage(message)

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
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                background-color: #333333;
                border: 1px solid #404040;
                border-radius: 6px;
                margin: 3px 2px;
                padding: 4px;
            }
            QListWidget::item:selected {
                background-color: #1a3d2a;
                border: 1px solid #00ff88;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
                border: 1px solid #555555;
            }
            QListWidget::item:hover:selected {
                background-color: #1f4a32;
                border: 1px solid #00ff88;
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
        main_layout.setContentsMargins(8, 5, 8, 2)
        main_layout.setSpacing(2)

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
        footer.setStyleSheet("color: #555555; font-size: 10px;")
        footer.setAlignment(Qt.AlignCenter)
        footer.setFixedHeight(16)
        main_layout.addWidget(footer)

        # Status bar at the bottom of the window
        self.statusBar().setStyleSheet(
            "QStatusBar { background: #1a1a2e; border-top: 1px solid #333; font-size: 12px; }"
        )
        self.set_statusbar("Ready")

    def create_search_tab(self) -> QWidget:
        """Create search tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 8, 10, 5)

        # Header
        header_layout = QHBoxLayout()

        title_label = QLabel(self.get_text('app_title'))
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #00ff88;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Search box
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.get_text('search_placeholder'))
        self.search_input.returnPressed.connect(self.do_search)

        # Paste button inside the search field (right-aligned via layout)
        paste_layout = QHBoxLayout(self.search_input)
        paste_layout.setContentsMargins(0, 0, 4, 0)
        paste_layout.addStretch()
        self.paste_btn = QToolButton()
        self.paste_btn.setText("📋")
        self.paste_btn.setToolTip("Paste URL from clipboard")
        self.paste_btn.setCursor(Qt.PointingHandCursor)
        self.paste_btn.setFixedSize(28, 28)
        self.paste_btn.setStyleSheet(
            "QToolButton { border: none; background: transparent; font-size: 18px; }"
            "QToolButton:hover { background: rgba(255,255,255,0.1); border-radius: 4px; }"
        )
        self.paste_btn.clicked.connect(self.paste_from_clipboard)
        paste_layout.addWidget(self.paste_btn)
        self.search_input.setTextMargins(0, 0, 32, 0)
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

        # Select all/deselect all bar (hidden by default, shown for playlists)
        self.select_bar = QWidget()
        self.select_bar.setFixedHeight(32)
        select_bar_layout = QHBoxLayout(self.select_bar)
        select_bar_layout.setContentsMargins(0, 2, 0, 2)
        select_bar_layout.setSpacing(4)
        _sel_btn_style = "font-size: 11px; padding: 2px 8px; border-radius: 3px;"
        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setStyleSheet(_sel_btn_style)
        self.select_all_btn.clicked.connect(self.select_all_videos)
        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.setStyleSheet(_sel_btn_style)
        self.deselect_all_btn.clicked.connect(self.deselect_all_videos)
        self.download_selected_btn = QPushButton("Download (0)")
        self.download_selected_btn.setStyleSheet(
            "font-size: 11px; padding: 2px 10px; border-radius: 3px; "
            "background-color: #00aa44; color: white; font-weight: bold;"
        )
        self.download_selected_btn.clicked.connect(self.download_selected_videos)
        select_bar_layout.addWidget(self.select_all_btn)
        select_bar_layout.addWidget(self.deselect_all_btn)
        select_bar_layout.addStretch()
        select_bar_layout.addWidget(self.download_selected_btn)
        self.select_bar.hide()
        left_layout.addWidget(self.select_bar)

        self.results_list = QListWidget()
        self.results_list.setMinimumWidth(450)
        self.results_list.itemClicked.connect(self.on_video_selected)
        left_layout.addWidget(self.results_list)

        self.load_more_btn = QPushButton(self.get_text('load_more'))
        self.load_more_btn.setObjectName("secondaryBtn")
        self.load_more_btn.clicked.connect(self.load_more_results)
        self.load_more_btn.hide()
        left_layout.addWidget(self.load_more_btn)

        self._search_result_count = 10

        splitter.addWidget(left_widget)

        # Right - Preview and options
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)

        # Preview
        preview_group = QGroupBox(self.get_text('preview'))
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setSpacing(4)
        preview_layout.setContentsMargins(8, 8, 8, 4)

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
        self.preview_thumbnail.setMinimumSize(260, 146)
        self.preview_thumbnail.setMaximumSize(320, 180)
        self.preview_thumbnail.setScaledContents(False)
        self.preview_thumbnail.setStyleSheet("background-color: #2d2d2d; border-radius: 8px;")
        self.preview_thumbnail.setAlignment(Qt.AlignCenter)
        self.preview_thumbnail.setText(f"🎬\n\n{self.get_text('select_video')}")
        self.preview_thumbnail.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        preview_layout.addWidget(self.preview_thumbnail, alignment=Qt.AlignCenter)

        # === PREVIEW PLAYER CONTROLS (single row) ===
        # Layout: [Play/Stop] [time] [===seeker===] [time] [vol] [vol_slider]
        preview_controls_layout = QHBoxLayout()
        preview_controls_layout.setSpacing(6)
        preview_controls_layout.setContentsMargins(0, 4, 0, 4)

        # Play/Stop button (icon-based)
        self.preview_play_btn = QPushButton()
        self.preview_play_btn.setFixedSize(32, 32)
        self.preview_play_btn.setToolTip("Play / Stop")
        self.preview_play_btn.clicked.connect(self.toggle_preview_play)
        self.preview_play_btn.setEnabled(False)
        self.preview_is_playing = False

        # Load play/stop icons
        self._play_icon = QIcon(os.path.join(APP_DIR, "Icons", ICON_DIR, "play_32x32.png"))
        self._stop_icon = QIcon(os.path.join(APP_DIR, "Icons", ICON_DIR, "stop_32x32.png"))
        self.preview_play_btn.setIcon(self._play_icon)
        self.preview_play_btn.setIconSize(QSize(20, 20))
        self.preview_play_btn.setStyleSheet("""
            QPushButton { background-color: transparent; border: none; }
            QPushButton:hover { background-color: rgba(0, 255, 136, 30); border-radius: 4px; }
            QPushButton:disabled { opacity: 0.3; }
        """)
        preview_controls_layout.addWidget(self.preview_play_btn)

        self.preview_time_current = QLabel("0:00")
        self.preview_time_current.setStyleSheet("color: #00ff88; font-size: 11px; min-width: 30px;")
        preview_controls_layout.addWidget(self.preview_time_current)

        self.preview_seek_slider = ClickableSlider(Qt.Horizontal)
        self.preview_seek_slider.setRange(0, 100)
        self.preview_seek_slider.setMinimumHeight(20)
        self.preview_seek_slider.sliderMoved.connect(self.preview_seek_position)
        self.preview_seek_slider.sliderPressed.connect(lambda: setattr(self, 'preview_slider_pressed_flag', True))
        self.preview_seek_slider.sliderReleased.connect(self.preview_slider_released)
        preview_controls_layout.addWidget(self.preview_seek_slider, 1)

        self.preview_time_total = QLabel("0:00")
        self.preview_time_total.setStyleSheet("color: #888888; font-size: 11px; min-width: 30px;")
        preview_controls_layout.addWidget(self.preview_time_total)

        self.preview_volume_slider = QSlider(Qt.Horizontal)
        self.preview_volume_slider.setRange(0, 100)
        self.preview_volume_slider.setValue(70)
        self.preview_volume_slider.setFixedWidth(60)
        self.preview_volume_slider.setMinimumHeight(20)
        self.preview_volume_slider.valueChanged.connect(self.change_preview_volume)
        preview_controls_layout.addWidget(self.preview_volume_slider)

        self.preview_volume_label = QLabel("70%")
        self.preview_volume_label.setStyleSheet("color: #888888; font-size: 11px; min-width: 30px;")
        preview_controls_layout.addWidget(self.preview_volume_label)

        preview_layout.addLayout(preview_controls_layout)
        # === END PREVIEW CONTROLS ===

        right_layout.addWidget(preview_group)

        # Format GroupBox - single line inside: [Video] [Audio] | Quality: [combo]
        format_group = QGroupBox(self.get_text('format'))
        format_row = QHBoxLayout(format_group)
        format_row.setContentsMargins(8, 4, 8, 4)
        format_row.setSpacing(6)

        self.type_group = QButtonGroup()
        self.video_radio = QRadioButton(self.get_text('video'))
        self.video_radio.setChecked(True)
        self.video_radio.toggled.connect(self.update_quality_options)
        self.type_group.addButton(self.video_radio)
        format_row.addWidget(self.video_radio)

        self.audio_radio = QRadioButton(self.get_text('audio'))
        self.audio_radio.toggled.connect(self.update_quality_options)
        self.type_group.addButton(self.audio_radio)
        format_row.addWidget(self.audio_radio)

        quality_label = QLabel(self.get_text('quality'))
        quality_label.setStyleSheet("margin-left: 8px;")
        format_row.addWidget(quality_label)

        self.quality_combo = QComboBox()
        self.update_quality_options()
        format_row.addWidget(self.quality_combo, 1)

        right_layout.addWidget(format_group)

        # Status GroupBox: label above progress bar
        status_group = QGroupBox(self.get_text('status'))
        status_layout = QVBoxLayout(status_group)
        status_layout.setContentsMargins(8, 4, 8, 4)
        status_layout.setSpacing(4)

        self.status_label = QLabel(self.get_text('waiting'))
        self.status_label.setStyleSheet("font-size: 11px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(16)
        status_layout.addWidget(self.progress_bar)

        right_layout.addWidget(status_group)

        # Push download button to bottom
        right_layout.addStretch()

        # Download button - at the bottom
        self.download_btn = QPushButton(self.get_text('download_btn'))
        self.download_btn.setObjectName("downloadBtn")
        self.download_btn.setMinimumHeight(50)
        self.download_btn.clicked.connect(self.do_download)
        self.download_btn.setEnabled(False)
        right_layout.addWidget(self.download_btn)

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
        self.downloads_table.setColumnWidth(3, 120)
        self.downloads_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.downloads_table.verticalHeader().setVisible(False)
        self.downloads_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.downloads_table.customContextMenuRequested.connect(self.show_download_context_menu)

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
        # Wrap in scroll area for small screens
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

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

        self.continue_playing_tray_checkbox = QCheckBox(self.get_text('continue_playing_tray'))
        self.continue_playing_tray_checkbox.setChecked(self.settings.value("continue_playing_tray", False, type=bool))
        appearance_layout.addWidget(self.continue_playing_tray_checkbox)

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

        # Download location
        location_layout = QHBoxLayout()
        location_label = QLabel(self.get_text('download_location'))
        location_layout.addWidget(location_label)

        self.location_path_label = QLabel(self.output_path)
        self.location_path_label.setStyleSheet("color: #aaaaaa; min-width: 200px;")
        location_layout.addWidget(self.location_path_label, 1)

        browse_btn = QPushButton(self.get_text('browse'))
        browse_btn.setObjectName("secondaryBtn")
        browse_btn.clicked.connect(self.browse_folder)
        location_layout.addWidget(browse_btn)

        downloads_layout.addLayout(location_layout)

        simultaneous_layout = QHBoxLayout()
        simultaneous_label = QLabel(self.get_text('simultaneous'))
        simultaneous_layout.addWidget(simultaneous_label)

        self.simultaneous_spin = QSpinBox()
        self.simultaneous_spin.setRange(1, 10)
        self.simultaneous_spin.setValue(self.settings.value("simultaneous_downloads", 2, type=int))
        simultaneous_layout.addWidget(self.simultaneous_spin)
        simultaneous_layout.addStretch()
        downloads_layout.addLayout(simultaneous_layout)

        self.auto_play_checkbox = QCheckBox(self.get_text('auto_play'))
        self.auto_play_checkbox.setChecked(self.settings.value("auto_play", False, type=bool))
        downloads_layout.addWidget(self.auto_play_checkbox)

        # Browser cookies for age-restricted videos
        cookies_layout = QHBoxLayout()
        cookies_label = QLabel("Browser cookies:")
        cookies_label.setToolTip("Uses your browser's cookies to access age-restricted videos and avoid bot detection.\nAuto-detected on first run. Change if you use a different browser for YouTube.")
        cookies_layout.addWidget(cookies_label)

        self.cookies_browser_combo = QComboBox()
        self.cookies_browser_combo.addItem("None (disabled)", "")
        self.cookies_browser_combo.addItem("Firefox", "firefox")
        self.cookies_browser_combo.addItem("Chrome", "chrome")
        self.cookies_browser_combo.addItem("Chromium", "chromium")
        self.cookies_browser_combo.addItem("Brave", "brave")
        self.cookies_browser_combo.addItem("Edge", "edge")

        saved_browser = self.settings.value("cookies_browser", None)
        if saved_browser is None:
            # First run - auto-detect browser
            saved_browser = self.detect_default_browser()
            self.settings.setValue("cookies_browser", saved_browser)
        for i in range(self.cookies_browser_combo.count()):
            if self.cookies_browser_combo.itemData(i) == saved_browser:
                self.cookies_browser_combo.setCurrentIndex(i)
                break

        cookies_layout.addWidget(self.cookies_browser_combo)
        cookies_layout.addStretch()
        downloads_layout.addLayout(cookies_layout)

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

        scroll.setWidget(tab)
        return scroll

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
        github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/NeleBiH/BalkGrab/")))
        links_layout.addWidget(github_btn)

        bug_btn = QPushButton(self.get_text('report_bug'))
        bug_btn.setObjectName("secondaryBtn")
        bug_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/NeleBiH/BalkGrab/issues")))
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

            # Load icon from file or use fallback (platform-aware)
            if sys.platform == "win32":
                icon_path = os.path.join(APP_DIR, "Icons", "windows", "icon.ico")
                if not os.path.exists(icon_path):
                    icon_path = os.path.join(APP_DIR, "Icons", "windows", "icon_64x64.png")
            else:
                icon_path = os.path.join(APP_DIR, "Icons", "linux", "icon_64x64.png")
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
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
            self.showNormal()
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
        self.signals.playlist_info.connect(self.on_playlist_info)

        # Clipboard monitoring for YouTube URLs
        self._clipboard = QApplication.clipboard()
        self._clipboard.dataChanged.connect(self.on_clipboard_changed)

        # Preview player signals
        self.preview_player.positionChanged.connect(self.on_preview_position_changed)
        self.preview_player.durationChanged.connect(self.on_preview_duration_changed)
        self.preview_player.playbackStateChanged.connect(self.on_preview_state_changed)
        self.preview_player.mediaStatusChanged.connect(self.on_preview_media_status)

    def load_settings(self):
        """Load saved settings"""
        pass  # Already loaded in __init__

    def save_settings(self):
        """Save settings"""
        new_lang = self.language_combo.currentData()

        self.settings.setValue("language", new_lang)
        self.settings.setValue("show_tray", self.tray_checkbox.isChecked())
        self.settings.setValue("minimize_to_tray", self.minimize_tray_checkbox.isChecked())
        self.settings.setValue("continue_playing_tray", self.continue_playing_tray_checkbox.isChecked())
        self.settings.setValue("start_minimized", self.start_minimized_checkbox.isChecked())
        self.settings.setValue("notifications", self.notifications_checkbox.isChecked())
        self.settings.setValue("simultaneous_downloads", self.simultaneous_spin.value())
        self.settings.setValue("auto_play", self.auto_play_checkbox.isChecked())
        self.settings.setValue("output_path", self.output_path)
        self.settings.setValue("cookies_browser", self.cookies_browser_combo.currentData())

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
        self.set_statusbar(self.get_text('settings_saved'))

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
            self.location_path_label.setText(folder)

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

    @staticmethod
    def is_youtube_url(text: str) -> bool:
        """Check if text is a valid YouTube URL (not just containing youtube in random text)"""
        t = text.lower()
        if not (t.startswith('http://') or t.startswith('https://') or t.startswith('www.')):
            return False
        return 'youtube.com/watch' in t or 'youtu.be/' in t or 'youtube.com/playlist' in t

    def paste_from_clipboard(self):
        """Paste clipboard content into search field"""
        text = QApplication.clipboard().text().strip()
        if text:
            self.search_input.setText(text)
            self.search_input.setFocus()
            # Auto-search if it's a YouTube URL
            if self.is_youtube_url(text):
                self.do_search()

    def on_clipboard_changed(self):
        """Auto-detect YouTube URLs in clipboard"""
        text = QApplication.clipboard().text().strip()
        if text and self.is_youtube_url(text):
            # Only intercept if search field is empty or has old content
            current = self.search_input.text().strip()
            if current != text:
                self.search_input.setText(text)
                self.set_statusbar("YouTube link detected in clipboard!")
                log.info(f"📋 Clipboard intercepted: {text[:60]}...")

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

        self._playlist_mode = False
        self.select_bar.hide()
        self._search_result_count = 10
        self.search_btn.setEnabled(False)
        self.search_btn.setText(self.get_text('searching'))
        self.load_more_btn.hide()
        self.results_list.clear()
        self.status_label.setText(self.get_text('searching'))

        self.set_statusbar("Searching YouTube...")
        self.search_worker = SearchWorker(query, self.signals, self._search_result_count)
        self.search_worker.start()

    def load_more_results(self):
        """Load more search results"""
        query = self.search_input.text().strip()
        if not query:
            return

        self._search_result_count += 10
        self.load_more_btn.setEnabled(False)
        self.load_more_btn.setText("Loading...")
        self.search_btn.setEnabled(False)

        self.search_worker = SearchWorker(query, self.signals, self._search_result_count)
        self.search_worker.start()

    def set_direct_url(self, url: str):
        """Set direct URL as selected video, detect playlists"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        # Detect playlist URL - fetch playlist info in background
        if 'list' in params or 'start_radio' in params:
            self.results_list.clear()
            self.load_more_btn.hide()
            self.status_label.setText(self.get_text('playlist_loading'))
            self.search_btn.setEnabled(False)
            self.search_btn.setText(self.get_text('searching'))
            self.set_statusbar("Playlist detected - fetching video list, please wait...")
            threading.Thread(target=self.fetch_playlist_info, args=(url,), daemon=True).start()
            return

        url = self.clean_youtube_url(url)
        self.results_list.clear()
        self.load_more_btn.hide()
        self.status_label.setText("Loading video info...")
        self.search_btn.setEnabled(False)
        self.search_btn.setText(self.get_text('searching'))
        threading.Thread(target=self.fetch_video_info, args=(url,), daemon=True).start()

    @staticmethod
    def clean_youtube_url(url: str) -> str:
        """Remove playlist parameters from YouTube URL to get single video only"""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        # Keep only the video ID parameter, remove list/index/playlist stuff
        clean_params = {}
        if 'v' in params:
            clean_params['v'] = params['v'][0]
        if clean_params:
            clean_query = urlencode(clean_params)
            return urlunparse(parsed._replace(query=clean_query))
        # For youtu.be short URLs, just strip query params
        if 'youtu.be' in parsed.netloc:
            return urlunparse(parsed._replace(query=''))
        return url

    @staticmethod
    def detect_default_browser() -> str:
        """Auto-detect which browser is available for cookies"""
        browser_paths = {
            'firefox': os.path.expanduser('~/.mozilla/firefox'),
            'chrome': os.path.expanduser('~/.config/google-chrome'),
            'chromium': os.path.expanduser('~/.config/chromium'),
            'brave': os.path.expanduser('~/.config/BraveSoftware/Brave-Browser'),
            'edge': os.path.expanduser('~/.config/microsoft-edge'),
        }
        if sys.platform == 'win32':
            browser_paths = {
                'firefox': os.path.join(os.environ.get('APPDATA', ''), 'Mozilla', 'Firefox', 'Profiles'),
                'chrome': os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google', 'Chrome', 'User Data'),
                'edge': os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Edge', 'User Data'),
                'brave': os.path.join(os.environ.get('LOCALAPPDATA', ''), 'BraveSoftware', 'Brave-Browser', 'User Data'),
            }
        for browser, path in browser_paths.items():
            if os.path.isdir(path):
                return browser
        return ""

    def fetch_playlist_info(self, url: str):
        """Fetch playlist info in background thread"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'remote_components': ['ejs:github'],
            }
            cookies_browser = self.settings.value("cookies_browser", "", type=str)
            if cookies_browser:
                ydl_opts['cookiesfrombrowser'] = (cookies_browser,)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            videos = []
            if 'entries' in info and info['entries']:
                for entry in info['entries']:
                    if entry:
                        video = {
                            'id': entry.get('id', ''),
                            'title': entry.get('title', 'Unknown'),
                            'url': entry.get('url', f"https://www.youtube.com/watch?v={entry.get('id', '')}"),
                            'thumbnail': entry.get('thumbnail', entry.get('thumbnails', [{}])[0].get('url', '') if entry.get('thumbnails') else ''),
                            'duration': entry.get('duration', 0),
                            'channel': entry.get('channel', entry.get('uploader', 'Unknown')),
                        }
                        videos.append(video)

            log.info(f"📋 Playlist info: {len(videos)} videos found")
            self.signals.playlist_info.emit(url, videos)

        except Exception as e:
            log.error(f"Error fetching playlist info: {e}")
            self.signals.playlist_info.emit(url, [])

    @Slot(str, list)
    def on_playlist_info(self, url: str, videos: list):
        """Handle playlist info - show dialog with options"""
        self.search_btn.setEnabled(True)
        self.search_btn.setText(self.get_text('search_btn'))

        if not videos:
            # Couldn't fetch playlist info, fall back to single video
            clean_url = self.clean_youtube_url(url)
            self.status_label.setText("Loading video info...")
            self.search_btn.setEnabled(False)
            self.search_btn.setText(self.get_text('searching'))
            self.set_statusbar("Could not fetch playlist - loading single video...")
            threading.Thread(target=self.fetch_video_info, args=(clean_url,), daemon=True).start()
            return

        count = len(videos)
        self.set_statusbar(f"Playlist loaded - {count} videos found")

        # Build custom dialog with dropdown for large playlists
        dialog = QDialog(self)
        dialog.setWindowTitle(self.get_text('playlist_detected'))
        dialog.setMinimumWidth(350)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)

        # Info label
        info_label = QLabel(self.get_text('playlist_msg', count=count))
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # "Show First Video" button
        first_btn = QPushButton(self.get_text('playlist_first_video'))
        layout.addWidget(first_btn)

        # Playlist load section: dropdown + load button
        playlist_row = QHBoxLayout()
        combo = QComboBox()
        if count > 20:
            combo.addItem(self.get_text('playlist_load_first', count=20), 20)
        if count > 50:
            combo.addItem(self.get_text('playlist_load_first', count=50), 50)
        if count > 100:
            combo.addItem(self.get_text('playlist_load_first', count=100), 100)
        warning = " \u26a0\ufe0f" if count > 100 else ""
        combo.addItem(self.get_text('playlist_load_all', count=count) + warning, count)
        playlist_row.addWidget(combo, 1)

        load_btn = QPushButton(self.get_text('playlist_load_btn'))
        playlist_row.addWidget(load_btn)
        layout.addLayout(playlist_row)

        # Warning label for very large playlists
        if count > 100:
            warn_label = QLabel("\u26a0\ufe0f " + self.get_text('playlist_warning'))
            warn_label.setStyleSheet("color: #ff6b6b; font-size: 11px;")
            layout.addWidget(warn_label)

        # Cancel button
        cancel_btn = QPushButton(self.get_text('playlist_cancel'))
        layout.addWidget(cancel_btn)

        result = {'action': None, 'count': 0}

        def on_first():
            result['action'] = 'first'
            dialog.accept()

        def on_load():
            result['action'] = 'playlist'
            result['count'] = combo.currentData()
            dialog.accept()

        first_btn.clicked.connect(on_first)
        load_btn.clicked.connect(on_load)
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()

        if result['action'] == 'first':
            clean_url = self.clean_youtube_url(url)
            self.results_list.clear()
            self.load_more_btn.hide()
            self.status_label.setText("Loading video info...")
            self.search_btn.setEnabled(False)
            self.search_btn.setText(self.get_text('searching'))
            self.set_statusbar("Loading first video from playlist...")
            threading.Thread(target=self.fetch_video_info, args=(clean_url,), daemon=True).start()
        elif result['action'] == 'playlist':
            load_count = result['count']
            self._playlist_mode = True
            self.results_list.clear()
            self.load_more_btn.hide()
            self.set_statusbar(f"Loading {load_count} videos from playlist...")
            self.signals.search_results.emit(videos[:load_count])
        else:
            self.set_statusbar("Ready")
            self.status_label.setText(self.get_text('waiting'))

    def fetch_video_info(self, url: str):
        """Fetch video info from URL"""
        try:
            ydl_opts = {
                'quiet': True,
                'noplaylist': True,
                'remote_components': ['ejs:github'],
            }
            cookies_browser = self.settings.value("cookies_browser", "", type=str)
            if cookies_browser:
                ydl_opts['cookiesfrombrowser'] = (cookies_browser,)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            # Safety: if playlist leaked through despite noplaylist, use first entry
            if 'entries' in info and info['entries']:
                info = info['entries'][0]

            video = {
                'url': url,
                'title': info.get('title', 'Unknown'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'channel': info.get('channel', 'Unknown'),
                'id': info.get('id', ''),
            }

            # Emit as search result so video appears in the list
            self.signals.search_results.emit([video])

        except Exception as e:
            error_msg = str(e)
            log.error(f"Error fetching video info: {error_msg}")
            # Store error for status bar display (will be shown when empty results arrive)
            short_msg = error_msg.split(': ')[-1] if ': ' in error_msg else error_msg
            self._last_fetch_error = short_msg
            self.signals.search_results.emit([])


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
        self.load_more_btn.setEnabled(True)
        self.load_more_btn.setText(self.get_text('load_more'))
        self.current_videos = videos
        self.thumbnail_workers.clear()
        self.results_list.clear()

        if not videos:
            error = getattr(self, '_last_fetch_error', None)
            if error:
                self.status_label.setText(self.get_text('no_results'))
                self.set_statusbar(f"Video error: {error}", error=True)
                self._last_fetch_error = None
            else:
                self.status_label.setText(self.get_text('no_results'))
                self.set_statusbar("No results found")
            self.load_more_btn.hide()
            return

        self.status_label.setText(self.get_text('found_videos', count=len(videos)))

        # Reset thumbnail progress tracking
        self._thumbnail_total = 0
        self._thumbnail_loaded = 0

        for i, video in enumerate(videos):
            item = QListWidgetItem()
            widget = VideoItemWidget(video)
            item.setSizeHint(QSize(self.results_list.width() - 30, 110))
            item.setData(Qt.UserRole, i)
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, widget)

            # Auto-check all in playlist mode, connect checkbox signal
            if self._playlist_mode:
                widget.checkbox.setChecked(True)
            widget.checkbox.stateChanged.connect(self.update_selection_count)

            if video.get('thumbnail'):
                self._thumbnail_total += 1
                worker = ThumbnailWorker(i, video['thumbnail'], self.signals)
                self.thumbnail_workers.append(worker)
                worker.start()

        # Show thumbnail loading progress in statusbar
        if self._thumbnail_total > 0:
            self.set_statusbar(f"Loading thumbnails... 0/{self._thumbnail_total} (0%)")

        # Show select bar and update count for all results
        self.select_bar.show()
        self.update_selection_count()

        # Show Load More only for search results, not playlist mode
        if self._playlist_mode:
            self.load_more_btn.hide()
        elif len(videos) >= self._search_result_count:
            self.load_more_btn.show()
        else:
            self.load_more_btn.hide()

    @Slot(int, QPixmap)
    def on_thumbnail_ready(self, index: int, pixmap: QPixmap):
        """Handle thumbnail ready"""
        if index < self.results_list.count():
            item = self.results_list.item(index)
            widget = self.results_list.itemWidget(item)
            if widget and isinstance(widget, VideoItemWidget):
                widget.set_thumbnail(pixmap)

        # Update thumbnail loading progress
        self._thumbnail_loaded += 1
        if self._thumbnail_total > 0 and self._thumbnail_loaded < self._thumbnail_total:
            pct = int(self._thumbnail_loaded / self._thumbnail_total * 100)
            self.set_statusbar(f"Loading thumbnails... {self._thumbnail_loaded}/{self._thumbnail_total} ({pct}%)")
        elif self._thumbnail_total > 0 and self._thumbnail_loaded >= self._thumbnail_total:
            if self._playlist_mode:
                self.update_selection_count()
            else:
                self.set_statusbar(f"Found {len(self.current_videos)} videos - thumbnails loaded")

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

            # If a single download was tracked, let it continue in background
            # and reset the button for the newly selected video
            if self._active_download_id:
                self._active_download_id = None
                self.download_btn.setText(self.get_text('download_btn'))
                self.download_btn.setStyleSheet("")

            self.download_btn.setEnabled(True)
            self.preview_play_btn.setEnabled(True)
            self.status_label.setText(self.get_text('ready_download'))
            self.stop_preview()  # Reset preview

    # ============ PLAYLIST SELECTION METHODS ============
    def update_selection_count(self):
        """Update status bar with number of selected videos"""
        count = 0
        for row in range(self.results_list.count()):
            item = self.results_list.item(row)
            widget = self.results_list.itemWidget(item)
            if widget and isinstance(widget, VideoItemWidget) and widget.checkbox.isChecked():
                count += 1
        total = self.results_list.count()
        self.set_statusbar(f"{count} of {total} videos selected and ready to download")
        self.download_selected_btn.setText(f"Download ({count})")
        self.download_selected_btn.setEnabled(count > 0)

    def select_all_videos(self):
        """Check all video checkboxes"""
        for row in range(self.results_list.count()):
            item = self.results_list.item(row)
            widget = self.results_list.itemWidget(item)
            if widget and isinstance(widget, VideoItemWidget):
                widget.checkbox.setChecked(True)
        self.update_selection_count()

    def deselect_all_videos(self):
        """Uncheck all video checkboxes"""
        for row in range(self.results_list.count()):
            item = self.results_list.item(row)
            widget = self.results_list.itemWidget(item)
            if widget and isinstance(widget, VideoItemWidget):
                widget.checkbox.setChecked(False)
        self.update_selection_count()

    def download_selected_videos(self):
        """Download checked videos respecting the simultaneous downloads limit"""
        selected = []
        for row in range(self.results_list.count()):
            item = self.results_list.item(row)
            widget = self.results_list.itemWidget(item)
            if widget and isinstance(widget, VideoItemWidget) and widget.checkbox.isChecked():
                index = item.data(Qt.UserRole)
                if index is not None and index < len(self.current_videos):
                    selected.append(self.current_videos[index])

        if not selected:
            return

        format_type = 'audio' if self.audio_radio.isChecked() else 'video'
        quality = self.quality_combo.currentText()

        for video in selected:
            url = video.get('url')
            if not url:
                video_id = video.get('id')
                if video_id:
                    url = f"https://www.youtube.com/watch?v={video_id}"
                else:
                    continue

            download = DownloadItem(
                url=url,
                title=video.get('title', 'Unknown'),
                output_path=self.output_path,
                format_type=format_type,
                quality=quality
            )
            self.downloads[download.id] = download
            self.add_download_to_table(download)
            self._download_queue.append(download.id)

        self._flush_download_queue()
        self.set_statusbar(f"Queued {len(selected)} videos for download")
        self.save_downloads()
        log.info(f"⬇️ Batch download queued: {len(selected)} videos")

    def _flush_download_queue(self):
        """Start downloads from queue up to the simultaneous downloads limit"""
        max_concurrent = self.settings.value("simultaneous_downloads", 2, type=int)
        active_count = len([
            did for did in self._active_batch_downloads
            if did in self.download_workers and self.download_workers[did].isRunning()
        ])
        cookies_browser = self.settings.value("cookies_browser", "", type=str)

        while self._download_queue and active_count < max_concurrent:
            download_id = self._download_queue.pop(0)
            if download_id in self.downloads:
                download = self.downloads[download_id]
                worker = DownloadWorker(download, self.signals, cookies_browser)
                self.download_workers[download_id] = worker
                self._active_batch_downloads.add(download_id)
                worker.start()
                active_count += 1
                log.info(f"⬇️ Starting queued download: {download.title}")

        if self._download_queue:
            log.info(f"⏳ {len(self._download_queue)} downloads waiting in queue")

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

        # Stop any other audio first
        self.stop_playback()

        url = self.selected_video.get('url')
        if not url:
            video_id = self.selected_video.get('id')
            if video_id:
                url = f"https://www.youtube.com/watch?v={video_id}"
            else:
                return

        self.preview_play_btn.setIcon(self._stop_icon)
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
                'remote_components': ['ejs:github'],
                'noplaylist': True,
            }
            cookies_browser = self.settings.value("cookies_browser", "", type=str)
            if cookies_browser:
                ydl_opts['cookiesfrombrowser'] = (cookies_browser,)
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
        self.preview_play_btn.setIcon(self._stop_icon)
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
        self._preview_auto_refreshing = False
        self._preview_stall_position = 0
        self._preview_last_position = -1
        self._preview_stall_count = 0
        self.preview_player.stop()
        self.preview_is_playing = False
        self._set_preview_btn_play()
        self.preview_seek_slider.setValue(0)
        self.preview_time_current.setText("0:00")
        if self.selected_video:
            self.status_label.setText(self.get_text('ready_download'))

    def _set_preview_btn_play(self):
        """Set preview button to play"""
        self.preview_play_btn.setIcon(self._play_icon)

    def preview_seek_position(self, position):
        """Seek preview"""
        if self.preview_player.duration() > 0:
            self.preview_player.setPosition(int(position * self.preview_player.duration() / 100))
            if self.preview_is_playing:
                self.status_label.setText("Buffering, please wait...")

    def preview_slider_released(self):
        """Handle slider release"""
        self.preview_slider_pressed_flag = False
        self.preview_seek_position(self.preview_seek_slider.value())

    def change_preview_volume(self, value):
        """Change preview volume"""
        self.preview_audio_output.setVolume(value / 100.0)
        self.preview_volume_label.setText(f"{value}%")

    def on_preview_position_changed(self, position):
        """Handle preview position - also detect stalls via timeout"""
        if self._preview_auto_refreshing:
            return  # Ignore position updates during stream refresh

        # Stall detection: if position hasn't changed for 5 consecutive updates (~5s)
        if self.preview_is_playing and position > 0:
            if position == self._preview_last_position:
                self._preview_stall_count += 1
                if self._preview_stall_count >= 5:
                    log.warning(f"Preview stall detected (position stuck at {position}ms for 5s)")
                    self._preview_stall_count = 0
                    # Trigger the same refresh as StalledMedia
                    self.on_preview_media_status(QMediaPlayer.MediaStatus.StalledMedia)
                    return
            else:
                self._preview_stall_count = 0
            self._preview_last_position = position

        if not self.preview_slider_pressed_flag and self.preview_player.duration() > 0:
            self.preview_seek_slider.setValue(int(position * 100 / self.preview_player.duration()))
        secs = position // 1000
        self.preview_time_current.setText(f"{secs // 60}:{secs % 60:02d}")

    def on_preview_duration_changed(self, duration):
        """Handle preview duration"""
        secs = duration // 1000
        self.preview_time_total.setText(f"{secs // 60}:{secs % 60:02d}")

    def on_preview_media_status(self, status):
        """Handle preview media status - detect stalls and auto-refresh stream"""
        if status == QMediaPlayer.MediaStatus.StalledMedia and not self._preview_auto_refreshing:
            log.warning("Preview stalled, fetching fresh stream URL...")
            self._preview_stall_position = self.preview_player.position()
            self._preview_auto_refreshing = True
            self.preview_play_btn.setIcon(self._stop_icon)
            self.preview_play_btn.setEnabled(False)
            self.status_label.setText("Refreshing stream...")

            # Re-fetch fresh stream URL
            url = self.selected_video.get('url', '')
            if not url:
                video_id = self.selected_video.get('id', '')
                if video_id:
                    url = f"https://www.youtube.com/watch?v={video_id}"
            if url:
                threading.Thread(target=self._fetch_stream_url, args=(url,), daemon=True).start()

        elif status == QMediaPlayer.MediaStatus.LoadedMedia and self._preview_auto_refreshing:
            # Fresh URL loaded, seek to where we left off
            log.info(f"Stream refreshed, resuming at {self._preview_stall_position}ms")
            self.preview_player.setPosition(self._preview_stall_position)
            self._preview_auto_refreshing = False
            self._preview_stall_position = 0
            self.preview_play_btn.setIcon(self._stop_icon)
            self.preview_play_btn.setEnabled(True)
            self.status_label.setText("Playing preview...")

        elif status == QMediaPlayer.MediaStatus.BufferedMedia:
            if self.preview_is_playing and not self._preview_auto_refreshing:
                self.status_label.setText("Playing preview...")

        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.preview_is_playing = False
            self._set_preview_btn_play()
            self.preview_seek_slider.setValue(0)
            self.preview_time_current.setText("0:00")

    def on_preview_state_changed(self, state):
        """Handle preview state"""
        if self._preview_auto_refreshing:
            return  # Ignore state changes during stream refresh
        if state == QMediaPlayer.PlaybackState.PlayingState:
            if self.preview_is_playing:
                self.status_label.setText("Playing preview...")
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self.preview_is_playing = False
            self._set_preview_btn_play()

    def do_download(self):
        """Start or stop download (dynamic button)"""
        # If download is active, stop it
        if hasattr(self, '_active_download_id') and self._active_download_id:
            self.stop_active_download()
            return

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
        self._active_download_id = download.id

        # Add to table
        self.add_download_to_table(download)

        # Start worker
        cookies_browser = self.settings.value("cookies_browser", "", type=str)
        worker = DownloadWorker(download, self.signals, cookies_browser)
        self.download_workers[download.id] = worker
        worker.start()

        # Update UI - button becomes Stop Download
        self.download_btn.setText(self.get_text('stop_download'))
        self.download_btn.setStyleSheet("background-color: #cc3333; color: white; font-weight: bold; font-size: 16px; border-radius: 8px;")
        self.status_label.setText(self.get_text('downloading', percent=0))

        self.set_statusbar(f"Downloading: {download.title}")
        log.info(f"⬇️ Started download: {download.title}")

    def stop_active_download(self):
        """Stop the currently active download"""
        if not hasattr(self, '_active_download_id') or not self._active_download_id:
            return

        download_id = self._active_download_id
        if download_id in self.download_workers:
            worker = self.download_workers[download_id]
            worker.cancel()
            log.info(f"⏹ Stopping download: {download_id}")

        self.set_statusbar("Download stopped")
        self._reset_download_btn()

    def _reset_download_btn(self):
        """Reset download button to normal state"""
        self._active_download_id = None
        self.download_btn.setText(self.get_text('download_btn'))
        self.download_btn.setStyleSheet("")  # Reset to default theme style
        self.download_btn.setEnabled(True if self.selected_video else False)

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

        # Action button (Cancel while downloading, Play/Stop when done)
        play_btn = QPushButton()
        play_btn.setProperty("download_id", download.id)
        play_btn.setProperty("btn_state", "idle")
        play_btn.clicked.connect(lambda checked, d=download, btn=play_btn: self.on_table_btn_clicked(d.id, btn))
        self.downloads_table.setCellWidget(row, 3, play_btn)

        # Set initial state based on whether loading from history
        if from_history:
            progress_bar.setValue(100)
            play_btn.setText("▶ Play")
            play_btn.setProperty("btn_state", "idle")
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
            play_btn.setText("✕ Cancel")
            play_btn.setProperty("btn_state", "downloading")
            play_btn.setEnabled(True)
            play_btn.setStyleSheet("color: #ff8800; font-weight: bold;")

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
                            title_item = self.downloads_table.item(row, 0)
                            fmt = title_item.data(Qt.UserRole + 1) if title_item else "audio"
                            if fmt == "audio":
                                status_item.setText("Converting...")
                            else:
                                status_item.setText("Merging...")
                            status_item.setForeground(QColor("#ffaa00"))
                    break

            # Update main progress bar
            self.progress_bar.setValue(int(percent))
            self.status_label.setText(self.get_text('downloading', percent=percent))
            title = self.downloads[download_id].title[:40]
            if status == "processing":
                fmt = self.downloads[download_id].format_type if download_id in self.downloads else "audio"
                if fmt == "audio":
                    self.set_statusbar(f"Converting audio: {title}...")
                else:
                    self.set_statusbar(f"Merging video: {title}...")
            else:
                self.set_statusbar(f"Downloading: {title} - {percent:.0f}%")

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
                        title_item = self.downloads_table.item(row, 0)
                        format_type = title_item.data(Qt.UserRole + 1) if title_item else "audio"
                        if format_type == "audio":
                            status_item.setText("Converted")
                            status_item.setForeground(QColor("#00ff88"))
                        else:
                            status_item.setText("Complete")
                            status_item.setForeground(QColor("#00aaff"))

                    play_btn = self.downloads_table.cellWidget(row, 3)
                    if play_btn:
                        play_btn.setText("▶ Play")
                        play_btn.setProperty("btn_state", "idle")
                        play_btn.setStyleSheet("")
                        play_btn.setEnabled(True)
                    break

        # Re-enable download button
        self._reset_download_btn()
        self.progress_bar.setValue(100)
        self.status_label.setText(self.get_text('done'))
        title = self.downloads[download_id].title[:50] if download_id in self.downloads else ""
        format_type = self.downloads[download_id].format_type if download_id in self.downloads else "audio"
        if format_type == "audio":
            self.set_statusbar(f"Download and conversion complete: {title}")
            notif_title = "Download & Conversion Complete"
        else:
            self.set_statusbar(f"Download complete: {title}")
            notif_title = "Download Complete"

        # Notification
        if self.settings.value("notifications", True, type=bool) and self.tray_icon:
            self.tray_icon.showMessage(
                notif_title,
                f"{self.downloads[download_id].title}",
                QSystemTrayIcon.Information,
                3000
            )

        # Auto-play
        if self.settings.value("auto_play", False, type=bool):
            self.play_downloaded(download_id)

        # Save downloads history
        self.save_downloads()

        # If this was a batch download, remove from active set and start next in queue
        if download_id in self._active_batch_downloads:
            self._active_batch_downloads.discard(download_id)
            self._flush_download_queue()

    @Slot(str, str)
    def on_download_error(self, download_id: str, error: str):
        """Handle download/search error"""
        log.error(f"❌ Download error: {error}")

        # Search errors don't have a download entry
        if download_id == "search":
            short_msg = error.split(': ')[-1] if ': ' in error else error
            self.set_statusbar(f"Search failed: {short_msg}", error=True)
            self.search_btn.setEnabled(True)
            self.search_btn.setText(self.get_text('search_btn'))
            self.status_label.setText(self.get_text('no_results'))
            return

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
                    play_btn = self.downloads_table.cellWidget(row, 3)
                    if play_btn:
                        play_btn.setText("▶ Play")
                        play_btn.setProperty("btn_state", "idle")
                        play_btn.setStyleSheet("")
                        play_btn.setEnabled(False)
                    break

        self._reset_download_btn()
        self.status_label.setText(self.get_text('error'))
        self.set_statusbar(f"Download failed: {error[:80]}", error=True)

        # If this was a batch download, remove from active set and start next in queue
        if download_id in self._active_batch_downloads:
            self._active_batch_downloads.discard(download_id)
            self._flush_download_queue()

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

                # Stop all other audio first
                self.stop_all_audio()
                self.media_player.setSource(QUrl.fromLocalFile(filepath))
                self.media_player.play()

                self.now_playing_label.setText(f"{self.get_text('now_playing')} {download.title}")
                self.player_is_playing = True
                self.position_timer.start(1000)
            else:
                log.warning(f"File not found: {filepath}")
                QMessageBox.warning(self, "File Not Found", f"Cannot find: {filepath}")

    def on_table_btn_clicked(self, download_id: str, btn: QPushButton):
        """Dispatch table action button click based on current btn_state"""
        state = btn.property("btn_state") or "idle"
        if state == "downloading":
            self._cancel_single_download(download_id, btn)
        else:
            self.toggle_download_play(download_id, btn)

    def _cancel_single_download(self, download_id: str, btn: QPushButton):
        """Cancel an in-progress download via the table button"""
        if download_id in self.download_workers:
            self.download_workers[download_id].cancel()
            log.info(f"✕ Cancelled download: {download_id}")

        btn.setText("▶ Play")
        btn.setProperty("btn_state", "idle")
        btn.setStyleSheet("")
        btn.setEnabled(False)

        for row in range(self.downloads_table.rowCount()):
            item = self.downloads_table.item(row, 0)
            if item and item.data(Qt.UserRole) == download_id:
                status_item = self.downloads_table.item(row, 2)
                if status_item:
                    status_item.setText("Cancelled")
                    status_item.setForeground(QColor("#888888"))
                break

        if download_id in self._active_batch_downloads:
            self._active_batch_downloads.discard(download_id)
            self._flush_download_queue()

        if self._active_download_id == download_id:
            self._reset_download_btn()
            self.set_statusbar("Download cancelled")

    def toggle_download_play(self, download_id: str, btn: QPushButton):
        """Toggle play/stop for a download item"""
        state = btn.property("btn_state") or "idle"

        if state == "playing":
            # Stop playback
            self.stop_playback()
        else:
            # Stop ALL audio first (preview + any other download)
            self.stop_all_audio()

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
                        btn.setProperty("btn_state", "playing")
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
                        btn.setProperty("btn_state", "playing")
                        self.current_playing_download_id = download_id
                        self.current_playing_btn = btn
                else:
                    QMessageBox.warning(self, "File Not Found", f"Cannot find: {filepath}")

    def stop_all_audio(self):
        """Stop ALL audio sources - preview, downloads player, external player"""
        # Stop preview if playing
        if self.preview_is_playing:
            self.stop_preview()

        # Stop downloads player
        self.stop_playback()

    def stop_playback(self):
        """Stop downloads playback"""
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
            self.current_playing_btn.setProperty("btn_state", "idle")
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

            # Monitor external player so we reset button when it closes
            if not hasattr(self, '_ext_player_timer'):
                self._ext_player_timer = QTimer(self)
                self._ext_player_timer.timeout.connect(self._check_external_player)
            self._ext_player_timer.start(1000)
        except Exception as e:
            log.error(f"Failed to launch video player: {e}")
            QMessageBox.critical(self, "Error", f"Failed to launch video player:\n{e}")

    def kill_external_player(self):
        """Kill external player process if running"""
        if self.external_player_process:
            try:
                self.external_player_process.terminate()
                self.external_player_process.wait(timeout=1)
            except Exception:
                try:
                    self.external_player_process.kill()
                except Exception:
                    pass
            self.external_player_process = None
            log.info("Killed external player")

    def _check_external_player(self):
        """Check if external player has exited and reset button state"""
        if self.external_player_process is None:
            if hasattr(self, '_ext_player_timer'):
                self._ext_player_timer.stop()
            return

        retcode = self.external_player_process.poll()
        if retcode is not None:
            # Player has exited
            self.external_player_process = None
            if hasattr(self, '_ext_player_timer'):
                self._ext_player_timer.stop()
            log.info("External player closed, resetting button state")
            # Reset the play button in downloads table
            if self.current_playing_btn:
                self.current_playing_btn.setText("▶ Play")
                self.current_playing_btn.setProperty("btn_state", "idle")
                self.current_playing_btn = None
                self.current_playing_download_id = None
            self.now_playing_label.setText(f"{self.get_text('now_playing')} {self.get_text('nothing_playing')}")

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
        config_file = os.path.expanduser("~/.config/BalkGrab/config.json")
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            log.error(f"Failed to load config: {e}")
        return {}

    def save_app_config(self, config: dict):
        """Save app config to JSON"""
        config_file = os.path.expanduser("~/.config/BalkGrab/config.json")
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
        if state == QMediaPlayer.PlaybackState.StoppedState:
            self.player_is_playing = False
            self._set_player_btn_play()
            self.position_timer.stop()

    def _set_player_btn_play(self):
        """Reset the current playing button to Play state"""
        if self.current_playing_btn:
            self.current_playing_btn.setText("▶ Play")
            self.current_playing_btn.setProperty("btn_state", "idle")
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

    def show_download_context_menu(self, pos):
        """Show right-click context menu for downloads table"""
        row = self.downloads_table.rowAt(pos.y())
        if row < 0:
            return

        item = self.downloads_table.item(row, 0)
        if not item:
            return

        download_id = item.data(Qt.UserRole)
        if download_id not in self.downloads:
            return

        download = self.downloads[download_id]
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #2b2b2b; color: #ffffff; border: 1px solid #404040; padding: 4px; }
            QMenu::item { padding: 6px 20px; }
            QMenu::item:selected { background-color: #1a3d2a; }
            QMenu::separator { height: 1px; background: #404040; margin: 4px 8px; }
        """)

        file_exists = download.filepath and os.path.exists(download.filepath)
        is_done = download.status == 'done'

        # Play
        play_action = menu.addAction(f"▶ {self.get_text('ctx_play')}")
        play_action.setEnabled(file_exists and is_done)
        play_action.triggered.connect(lambda: self._ctx_play(download_id, row))

        menu.addSeparator()

        # Open containing folder
        open_action = menu.addAction(f"📂 {self.get_text('ctx_open_folder')}")
        open_action.setEnabled(file_exists)
        open_action.triggered.connect(lambda: self._ctx_open_folder(download))

        # Download again
        again_action = menu.addAction(f"⬇ {self.get_text('ctx_download_again')}")
        again_action.setEnabled(bool(download.url))
        again_action.triggered.connect(lambda: self._ctx_download_again(download))

        menu.addSeparator()

        # Convert to submenu
        convert_menu = menu.addMenu(f"🔄 {self.get_text('ctx_convert_to')}")
        convert_menu.setStyleSheet(menu.styleSheet())
        convert_menu.setEnabled(file_exists and is_done)
        for fmt in ['MP3', 'MP4', 'FLAC', 'WAV', 'OGG', 'AAC']:
            action = convert_menu.addAction(fmt)
            action.triggered.connect(lambda checked, f=fmt: self._ctx_convert(download, f))

        menu.addSeparator()

        # Remove from list
        remove_action = menu.addAction(f"🗑 {self.get_text('ctx_remove')}")
        remove_action.triggered.connect(lambda: self._ctx_remove(download_id, row))

        menu.exec(self.downloads_table.viewport().mapToGlobal(pos))

    def _ctx_play(self, download_id: str, row: int):
        """Context menu: Play downloaded file"""
        play_btn = self.downloads_table.cellWidget(row, 3)
        if play_btn:
            self.toggle_download_play(download_id, play_btn)

    def _ctx_open_folder(self, download: DownloadItem):
        """Context menu: Open containing folder"""
        if download.filepath and os.path.exists(download.filepath):
            folder = os.path.dirname(download.filepath)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _ctx_download_again(self, download: DownloadItem):
        """Context menu: Download again - switch to Search tab with URL"""
        if download.url:
            self.tab_widget.setCurrentIndex(0)
            self.search_input.setText(download.url)
            self.search_input.setFocus()
            self.do_search()

    def _ctx_convert(self, download: DownloadItem, target_fmt: str):
        """Context menu: Convert file using FFmpeg (background process with QTimer polling)"""
        if not download.filepath or not os.path.exists(download.filepath):
            return

        import subprocess

        source = download.filepath
        base, _ = os.path.splitext(source)
        ext = target_fmt.lower()
        dest = f"{base}.{ext}"

        # Don't convert to same format
        if source.lower().endswith(f".{ext}"):
            self.set_statusbar(f"Already in {target_fmt} format", error=True)
            return

        # Avoid overwriting
        if os.path.exists(dest):
            counter = 1
            while os.path.exists(f"{base}_{counter}.{ext}"):
                counter += 1
            dest = f"{base}_{counter}.{ext}"

        self.set_statusbar(self.get_text('converting_file', fmt=target_fmt))
        log.info(f"Converting: {source} → {dest}")

        cmd = ['ffmpeg', '-i', source, '-y']
        if ext == 'mp3':
            cmd.extend(['-codec:a', 'libmp3lame', '-b:a', '320k'])
        elif ext == 'aac':
            cmd.extend(['-codec:a', 'aac', '-b:a', '256k'])
        elif ext == 'flac':
            cmd.extend(['-codec:a', 'flac'])
        elif ext == 'wav':
            cmd.extend(['-codec:a', 'pcm_s16le'])
        elif ext == 'ogg':
            cmd.extend(['-codec:a', 'libvorbis', '-b:a', '256k'])
        elif ext == 'mp4':
            cmd.extend(['-codec:v', 'copy', '-codec:a', 'copy'])
        cmd.append(dest)

        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except FileNotFoundError:
            self.set_statusbar("FFmpeg not found - please install FFmpeg", error=True)
            return

        # Poll for completion with QTimer
        timer = QTimer(self)
        def check_done():
            if proc.poll() is not None:
                timer.stop()
                if proc.returncode == 0:
                    self.set_statusbar(self.get_text('conversion_done', fmt=target_fmt))
                    log.info(f"Conversion complete: {dest}")
                else:
                    stderr = proc.stderr.read().decode(errors='replace')[-200:] if proc.stderr else ""
                    self.set_statusbar(self.get_text('conversion_failed', error=stderr[:100]), error=True)
                    log.error(f"Conversion failed: {stderr}")
        timer.timeout.connect(check_done)
        timer.start(500)
        self._convert_timer = timer
        self._convert_proc = proc

    def _ctx_remove(self, download_id: str, row: int):
        """Context menu: Remove download from list"""
        # Stop playback if this item is playing
        if self.current_playing_download_id == download_id:
            self.stop_playback()

        self.downloads_table.removeRow(row)
        if download_id in self.downloads:
            del self.downloads[download_id]
        self.save_downloads()

        if self.downloads_table.rowCount() == 0:
            self.downloads_table.hide()
            self.downloads_placeholder.show()

        log.info(f"Removed download: {download_id}")

    def closeEvent(self, event):
        """Handle close event"""
        if self.settings.value("minimize_to_tray", False, type=bool) and self.tray_icon and self.tray_icon.isVisible():
            if not self.settings.value("continue_playing_tray", False, type=bool):
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
    app.setOrganizationName("BalkGrab")

    # Set application icon
    icon_path = os.path.join(APP_DIR, "Icons", ICON_DIR, "icon_256x256.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = BalkGrabGrabber()

    # Check start minimized
    settings = QSettings("BalkGrab", "BalkGrab")
    if settings.value("start_minimized", False, type=bool):
        window.hide()
    else:
        window.show()

    log.info("🚀 Application started!")
    log.info("-" * 50)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
