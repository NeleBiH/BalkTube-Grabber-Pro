"""Main window class for BalkGrab."""

import sys
import os
import json
import threading
import atexit
import requests
import logging
from pathlib import Path
from typing import Optional, List, Dict
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QComboBox, QProgressBar,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QGroupBox, QRadioButton, QButtonGroup, QFrame, QSplitter,
    QSizePolicy, QScrollArea, QTabWidget,
    QSlider, QCheckBox, QTextEdit, QTextBrowser, QSystemTrayIcon, QMenu,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox, QInputDialog,
    QDialog, QToolButton, QStyle
)
from PySide6.QtCore import (
    Qt, QSize, QMetaObject, Q_ARG,
    Slot, QUrl, QTimer, QSettings
)
from PySide6.QtGui import (
    QPixmap, QIcon, QColor, QAction, QDesktopServices, QPalette
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

import yt_dlp

from . import APP_VERSION, APP_NAME
from .constants import ICON_DIR
from .themes import get_theme, get_available_themes
from .translations import TRANSLATIONS
from .models import WorkerSignals, DownloadItem
from .workers import SearchWorker, ThumbnailWorker, DownloadWorker
from .widgets import ClickableSlider, VideoItemWidget

log = logging.getLogger("BalkGrab")


class BalkGrabGrabber(QMainWindow):
    """Main application window"""

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
        icon_path = os.path.join(ICON_DIR, "icon_256x256.png")
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
        self._download_row_map: Dict[str, int] = {}  # download_id -> table row for O(1) lookup
        self._selected_count = 0  # tracks checked video count for O(1) button updates
        self._last_fetch_error = None
        self._ext_player_timer = None
        self._convert_timer = None
        self._convert_proc = None
        self.search_worker = None

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
        self._preview_temp_path = None
        self._preview_all_temps: list = []  # all temp dirs created this session
        atexit.register(self._cleanup_all_preview_temps)

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
        """Setup theme based on saved preference"""
        theme = self.settings.value("theme", "dark")
        self.apply_theme(theme)

    def apply_theme(self, theme_id: str):
        """Apply the selected theme and update icons accordingly"""
        app = QApplication.instance()
        self._current_theme_id = theme_id
        theme = get_theme(theme_id)

        if theme is None:
            # System default — no custom stylesheet
            self.setStyleSheet("")
            app.setPalette(self.style().standardPalette())
            self._play_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)
            self._stop_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop)
        else:
            self.setStyleSheet(theme["stylesheet"])
            # Set app-wide palette for highlight colors (fixes KDE combo/menu highlighting)
            palette = app.palette()
            palette_map = {
                "Highlight": QPalette.ColorRole.Highlight,
                "HighlightedText": QPalette.ColorRole.HighlightedText,
                "Window": QPalette.ColorRole.Window,
                "WindowText": QPalette.ColorRole.WindowText,
                "Base": QPalette.ColorRole.Base,
                "Text": QPalette.ColorRole.Text,
            }
            for key, role in palette_map.items():
                if key in theme.get("palette", {}):
                    palette.setColor(role, QColor(theme["palette"][key]))
            app.setPalette(palette)
            # Use custom green icons for dark theme
            self._play_icon = QIcon(os.path.join(ICON_DIR, "play_32x32.png"))
            self._stop_icon = QIcon(os.path.join(ICON_DIR, "stop_32x32.png"))

        # Update preview play button icon
        if hasattr(self, 'preview_play_btn'):
            if hasattr(self, 'preview_is_playing') and self.preview_is_playing:
                self.preview_play_btn.setIcon(self._stop_icon)
            else:
                self.preview_play_btn.setIcon(self._play_icon)

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

        # Trailing actions inside search field (proper Qt way)
        # Paste action (always visible)
        paste_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton)
        self.paste_action = self.search_input.addAction(paste_icon, QLineEdit.ActionPosition.TrailingPosition)
        self.paste_action.setToolTip("Paste URL from clipboard")
        self.paste_action.triggered.connect(self.paste_from_clipboard)

        # Clear action (visible only when text is present)
        clear_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_LineEditClearButton)
        self.clear_action = self.search_input.addAction(clear_icon, QLineEdit.ActionPosition.TrailingPosition)
        self.clear_action.setToolTip("Clear")
        self.clear_action.setVisible(False)
        self.clear_action.triggered.connect(self.search_input.clear)
        self.search_input.textChanged.connect(lambda t: self.clear_action.setVisible(bool(t)))
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
        self.results_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_list.customContextMenuRequested.connect(self.show_video_context_menu)
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
        self.preview_thumbnail.setText(f"\U0001f3ac\n\n{self.get_text('select_video')}")
        self.preview_thumbnail.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        preview_layout.addWidget(self.preview_thumbnail, alignment=Qt.AlignCenter)

        # === PREVIEW PLAYER CONTROLS (single row) ===
        # Layout: [Play/Stop] [time] [===seeker===] [time] [vol] [vol_slider]
        preview_controls_layout = QHBoxLayout()
        preview_controls_layout.setSpacing(6)
        preview_controls_layout.setContentsMargins(0, 4, 0, 4)

        # Play/Stop button (icon-based)
        self.preview_play_btn = QPushButton()
        self.preview_play_btn.setObjectName("previewPlayBtn")
        self.preview_play_btn.setFixedSize(32, 32)
        self.preview_play_btn.setToolTip("Play / Stop")
        self.preview_play_btn.clicked.connect(self.toggle_preview_play)
        self.preview_play_btn.setEnabled(False)
        self.preview_is_playing = False

        # Icons are set by apply_theme() called from setup_dark_theme()
        self.preview_play_btn.setIcon(self._play_icon)
        self.preview_play_btn.setIconSize(QSize(20, 20))
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
        self.language_combo.addItem("\U0001f1ec\U0001f1e7 English", "en")
        self.language_combo.addItem("\U0001f1e9\U0001f1ea Deutsch", "de")
        self.language_combo.addItem("\U0001f1ed\U0001f1f7\U0001f1f7\U0001f1f8 Hrvatski/Srpski", "hr")

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

        # Theme dropdown
        theme_layout = QHBoxLayout()
        theme_label = QLabel(self.get_text('theme'))
        theme_layout.addWidget(theme_label)

        self.theme_combo = QComboBox()
        current_theme = self.settings.value("theme", "dark")
        for theme_id, theme_name in get_available_themes():
            # Use translation if available, otherwise use theme name
            tr_key = f"theme_{theme_id}"
            display = self.tr.get(tr_key, theme_name)
            self.theme_combo.addItem(display, theme_id)
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == current_theme:
                self.theme_combo.setCurrentIndex(i)
                break
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        appearance_layout.addLayout(theme_layout)

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

        self.clipboard_monitor_checkbox = QCheckBox(self.get_text('clipboard_monitor'))
        self.clipboard_monitor_checkbox.setChecked(self.settings.value("clipboard_monitor", True, type=bool))
        appearance_layout.addWidget(self.clipboard_monitor_checkbox)

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

        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel(self.get_text('speed_limit')))
        self.speed_limit_spin = QSpinBox()
        self.speed_limit_spin.setRange(0, 100000)
        self.speed_limit_spin.setSingleStep(500)
        self.speed_limit_spin.setValue(self.settings.value("speed_limit", 0, type=int))
        self.speed_limit_spin.setFixedWidth(90)
        speed_layout.addWidget(self.speed_limit_spin)
        speed_layout.addWidget(QLabel(self.get_text('speed_limit_unit')))
        speed_layout.addStretch()
        downloads_layout.addLayout(speed_layout)

        self.embed_metadata_checkbox = QCheckBox(self.get_text('embed_metadata'))
        self.embed_metadata_checkbox.setChecked(self.settings.value("embed_metadata", True, type=bool))
        downloads_layout.addWidget(self.embed_metadata_checkbox)

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

        # Header: icon + app name + version
        header = QHBoxLayout()
        header.setSpacing(15)
        header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        icon_label = QLabel()
        icon_path = os.path.join(ICON_DIR, "icon_256x256.png")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(
                64, 64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(64, 64)
        header.addWidget(icon_label)

        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title_label = QLabel("BalkGrab")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet("font-size: 13px; color: #888888;")
        title_layout.addWidget(title_label)
        title_layout.addWidget(version_label)
        title_layout.addStretch()
        header.addLayout(title_layout)
        header.addStretch()

        layout.addLayout(header)

        # About text - expands to fill space
        about_text = QTextBrowser()
        about_text.setReadOnly(True)
        about_text.setOpenExternalLinks(True)
        about_text.setHtml(self.get_text('about_description'))
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
        from PySide6.QtWidgets import QDialogButtonBox

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

            icon_path = os.path.join(ICON_DIR, "icon_64x64.png")
            if os.path.exists(icon_path):
                self.tray_icon.setIcon(QIcon(icon_path))
            else:
                pixmap = QPixmap(32, 32)
                pixmap.fill(QColor("#00ff88"))
                self.tray_icon.setIcon(QIcon(pixmap))

            # Menu
            self.tray_menu = QMenu()

            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show)
            self.tray_menu.addAction(show_action)

            self.tray_menu.addSeparator()

            quit_action = QAction("Quit", self)
            quit_action.triggered.connect(QApplication.quit)
            self.tray_menu.addAction(quit_action)

            self.tray_icon.setContextMenu(self.tray_menu)
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
        self.settings.setValue("clipboard_monitor", self.clipboard_monitor_checkbox.isChecked())
        self.settings.setValue("simultaneous_downloads", self.simultaneous_spin.value())
        self.settings.setValue("speed_limit", self.speed_limit_spin.value())
        self.settings.setValue("embed_metadata", self.embed_metadata_checkbox.isChecked())
        self.settings.setValue("auto_play", self.auto_play_checkbox.isChecked())
        self.settings.setValue("output_path", self.output_path)
        self.settings.setValue("cookies_browser", self.cookies_browser_combo.currentData())

        # Apply theme
        new_theme = self.theme_combo.currentData()
        self.settings.setValue("theme", new_theme)
        self.apply_theme(new_theme)

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
    def is_direct_url(text: str) -> bool:
        """Check if text is any valid URL that can be passed directly to yt-dlp"""
        t = text.lower()
        return t.startswith('http://') or t.startswith('https://')

    @staticmethod
    def is_youtube_video_url(url: str) -> bool:
        """Check if URL points to a specific YouTube video (not a channel/playlist)"""
        if 'youtube.com' in url:
            return 'watch?v=' in url or '/shorts/' in url or '/live/' in url
        if 'youtu.be/' in url:
            return True
        return False  # non-YouTube URLs are assumed to be direct video URLs

    @staticmethod
    def is_youtube_url(text: str) -> bool:
        """Check if text is specifically a YouTube URL"""
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
            if self.is_direct_url(text):
                self.do_search()

    def on_clipboard_changed(self):
        """Auto-detect video URLs in clipboard"""
        if not self.settings.value("clipboard_monitor", True, type=bool):
            return
        text = QApplication.clipboard().text().strip()
        if text and self.is_youtube_url(text):
            current = self.search_input.text().strip()
            if current != text:
                self.search_input.setText(text)
                self.set_statusbar("Video link detected in clipboard!")
                log.info(f"Clipboard intercepted: {text[:60]}...")

    def do_search(self):
        """Start search"""
        query = self.search_input.text().strip()
        log.info(f"Search: '{query}'")

        # Clear any error from previous search
        self._last_fetch_error = None

        if not query:
            QMessageBox.warning(self, "Empty Search", "Please enter something to search!")
            return

        if self.is_direct_url(query):
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
        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.quit()
            self.search_worker.wait(300)
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

        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.quit()
            self.search_worker.wait(300)
        self.search_worker = SearchWorker(query, self.signals, self._search_result_count)
        self.search_worker.start()

    def set_direct_url(self, url: str):
        """Set direct URL as selected video. YouTube: detect playlists. Other platforms: fetch directly."""
        is_yt = self.is_youtube_url(url)

        if is_yt:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
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

            log.info(f"Playlist info: {len(videos)} videos found")
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
                info = info['entries'][0] or {}

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
        log.info(f"Received {len(videos)} results")

        self.search_btn.setEnabled(True)
        self.search_btn.setText(self.get_text('search_btn'))
        self.load_more_btn.setEnabled(True)
        self.load_more_btn.setText(self.get_text('load_more'))
        self.current_videos = videos
        for _tw in self.thumbnail_workers:
            _tw.quit()
            _tw.wait(300)
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
            item.setSizeHint(QSize(max(200, self.results_list.width() - 30), 110))
            item.setData(Qt.UserRole, i)
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, widget)

            # Auto-check all in playlist mode, connect checkbox signal
            if self._playlist_mode:
                widget.checkbox.blockSignals(True)
                widget.checkbox.setChecked(True)
                widget.checkbox.blockSignals(False)
            widget.checkbox.stateChanged.connect(self._on_video_checkbox_changed)

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
            # In playlist mode, clicking the row toggles the checkbox
            if self._playlist_mode:
                widget = self.results_list.itemWidget(item)
                if widget and isinstance(widget, VideoItemWidget):
                    widget.checkbox.setChecked(not widget.checkbox.isChecked())
                return

            self.selected_video = self.current_videos[index]

            self.preview_title.setText(self.selected_video.get('title', 'Unknown'))

            duration = self.selected_video.get('duration', 0)
            if duration:
                duration = int(duration)
                duration_str = f"{duration // 60}:{duration % 60:02d}"
            else:
                duration_str = "N/A"

            self.preview_meta.setText(f"\U0001f4fa {self.selected_video.get('channel', '')} | \u23f1\ufe0f {duration_str}")

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
    def _on_video_checkbox_changed(self, state):
        """O(1) update when a single checkbox is toggled"""
        self._selected_count += 1 if int(state) == 2 else -1
        self._selected_count = max(0, self._selected_count)
        self._refresh_selection_ui()

    def _refresh_selection_ui(self):
        """Update button text and status bar from cached _selected_count"""
        total = self.results_list.count()
        self.set_statusbar(f"{self._selected_count} of {total} videos selected and ready to download")
        self.download_selected_btn.setText(f"Download ({self._selected_count})")
        self.download_selected_btn.setEnabled(self._selected_count > 0)

    def update_selection_count(self):
        """Full O(n) recount - call after bulk changes (new results, select/deselect all)"""
        count = 0
        for row in range(self.results_list.count()):
            item = self.results_list.item(row)
            widget = self.results_list.itemWidget(item)
            if widget and isinstance(widget, VideoItemWidget) and widget.checkbox.isChecked():
                count += 1
        self._selected_count = count
        self._refresh_selection_ui()

    def select_all_videos(self):
        """Check all video checkboxes"""
        for row in range(self.results_list.count()):
            item = self.results_list.item(row)
            widget = self.results_list.itemWidget(item)
            if widget and isinstance(widget, VideoItemWidget):
                widget.checkbox.blockSignals(True)
                widget.checkbox.setChecked(True)
                widget.checkbox.blockSignals(False)
        self._selected_count = self.results_list.count()
        self._refresh_selection_ui()

    def deselect_all_videos(self):
        """Uncheck all video checkboxes"""
        for row in range(self.results_list.count()):
            item = self.results_list.item(row)
            widget = self.results_list.itemWidget(item)
            if widget and isinstance(widget, VideoItemWidget):
                widget.checkbox.blockSignals(True)
                widget.checkbox.setChecked(False)
                widget.checkbox.blockSignals(False)
        self._selected_count = 0
        self._refresh_selection_ui()

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

            # Skip channel/playlist URLs
            if self.is_youtube_url(url) and not self.is_youtube_video_url(url):
                log.warning(f"Skipping channel/playlist URL: {url}")
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
        log.info(f"Batch download queued: {len(selected)} videos")
        # Reset checkboxes and button after queueing
        self.deselect_all_videos()

    def _flush_download_queue(self):
        """Start downloads from queue up to the simultaneous downloads limit"""
        max_concurrent = max(1, min(10, self.settings.value("simultaneous_downloads", 2, type=int)))
        cookies_browser = self.settings.value("cookies_browser", "", type=str)
        embed_metadata = self.settings.value("embed_metadata", True, type=bool)
        speed_limit = self.settings.value("speed_limit", 0, type=int)

        while self._download_queue:
            # O(1) - set is kept accurate by on_download_finished/on_download_error
            if len(self._active_batch_downloads) >= max_concurrent:
                break

            download_id = self._download_queue.pop(0)
            if download_id in self.downloads:
                download = self.downloads[download_id]
                worker = DownloadWorker(download, self.signals, cookies_browser, embed_metadata, speed_limit)
                self.download_workers[download_id] = worker
                self._active_batch_downloads.add(download_id)
                worker.start()
                log.info(f"Starting queued download: {download.title}")

        if self._download_queue:
            log.info(f"{len(self._download_queue)} downloads waiting in queue")

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
            import tempfile
            tmp_dir = tempfile.mkdtemp(prefix='balkgrab_preview_')
            self._preview_all_temps.append(tmp_dir)
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                # Lowest quality audio for fast preview download
                'format': 'bestaudio[ext=m4a][abr<=128]/bestaudio[ext=m4a]/bestaudio[abr<=128]/bestaudio/worst',
                'outtmpl': os.path.join(tmp_dir, 'preview.%(ext)s'),
                'noplaylist': True,
                'remote_components': ['ejs:github'],
            }
            cookies_browser = self.settings.value("cookies_browser", "", type=str)
            if cookies_browser:
                ydl_opts['cookiesfrombrowser'] = (cookies_browser,)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info)

            # Find the actual downloaded file (extension may differ)
            if not os.path.exists(filepath):
                files = [str(p) for p in Path(tmp_dir).iterdir() if p.is_file()]
                filepath = files[0] if files else None

            if filepath and os.path.exists(filepath):
                self._preview_temp_path = tmp_dir
                QMetaObject.invokeMethod(self, "_play_stream", Qt.QueuedConnection, Q_ARG(str, filepath))
            else:
                log.error("Preview temp file not found")
                import shutil; shutil.rmtree(tmp_dir, ignore_errors=True)
                QMetaObject.invokeMethod(self, "_preview_error", Qt.QueuedConnection)
        except Exception as e:
            log.error(f"Preview error: {e}")
            QMetaObject.invokeMethod(self, "_preview_error", Qt.QueuedConnection)

    @Slot(str)
    def _play_stream(self, stream_url: str):
        """Play stream from local temp file"""
        self.preview_player.setSource(QUrl.fromLocalFile(stream_url))
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
        self._cleanup_preview_temp()
        self.status_label.setText("Preview failed")

    def _cleanup_preview_temp(self):
        """Delete current temp preview file"""
        if self._preview_temp_path:
            import shutil
            shutil.rmtree(self._preview_temp_path, ignore_errors=True)
            self._preview_temp_path = None

    def _cleanup_all_preview_temps(self):
        """Delete all temp preview dirs (called by atexit on crash/close)"""
        import shutil
        for tmp_dir in self._preview_all_temps:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        self._preview_all_temps.clear()

    def stop_preview(self):
        """Stop preview"""
        self._preview_auto_refreshing = False
        self._preview_stall_position = 0
        self._preview_last_position = -1
        self._preview_stall_count = 0
        self.preview_player.stop()
        self.preview_player.setSource(QUrl())  # release file handle before deleting
        self.preview_is_playing = False
        self._set_preview_btn_play()
        self.preview_seek_slider.setValue(0)
        self.preview_time_current.setText("0:00")
        self._cleanup_preview_temp()
        if self.selected_video:
            self.status_label.setText(self.get_text('ready_download'))

    def _set_preview_btn_play(self):
        """Set preview button to play"""
        self.preview_play_btn.setIcon(self._play_icon)

    def preview_seek_position(self, position):
        """Seek preview"""
        duration = self.preview_player.duration()
        if duration > 0:
            self.preview_player.setPosition(int(position * duration / 100))
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

        duration = self.preview_player.duration()
        if not self.preview_slider_pressed_flag and duration > 0:
            self.preview_seek_slider.setValue(int(position * 100 / duration))
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

            # Re-fetch fresh stream URL - snapshot selected_video on GUI thread to avoid race
            _sv = self.selected_video
            if _sv:
                url = _sv.get('url', '')
                if not url:
                    video_id = _sv.get('id', '')
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
        if self._active_download_id:
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

        # Block channel/playlist URLs - would download entire channel
        if self.is_youtube_url(url) and not self.is_youtube_video_url(url):
            QMessageBox.warning(self, "Cannot Download",
                "This result is a channel or playlist, not a specific video.\n"
                "Please search for and select a specific video to download.")
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
        embed_metadata = self.settings.value("embed_metadata", True, type=bool)
        speed_limit = self.settings.value("speed_limit", 0, type=int)
        worker = DownloadWorker(download, self.signals, cookies_browser, embed_metadata, speed_limit)
        self.download_workers[download.id] = worker
        worker.start()

        # Update UI - button becomes Stop Download
        self.download_btn.setText(self.get_text('stop_download'))
        self.download_btn.setStyleSheet("background-color: #cc3333; color: white; font-weight: bold; font-size: 16px; border-radius: 8px;")
        self.status_label.setText(self.get_text('downloading', percent=0))

        self.set_statusbar(f"Downloading: {download.title}")
        log.info(f"Started download: {download.title}")

    def stop_active_download(self):
        """Stop the currently active download"""
        if not self._active_download_id:
            return

        download_id = self._active_download_id
        if download_id in self.download_workers:
            worker = self.download_workers[download_id]
            worker.cancel()
            log.info(f"Stopping download: {download_id}")

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
            play_btn.setText("\u25b6 Play")
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
            play_btn.setText("\u2715 Cancel")
            play_btn.setProperty("btn_state", "downloading")
            play_btn.setEnabled(True)
            play_btn.setStyleSheet("color: #ff8800; font-weight: bold;")

        self.downloads_table.setRowHeight(row, 55)
        self._download_row_map[download.id] = row

    def _rebuild_row_map(self):
        """Rebuild the download_id->row map after row removals."""
        self._download_row_map.clear()
        for r in range(self.downloads_table.rowCount()):
            item = self.downloads_table.item(r, 0)
            if item:
                did = item.data(Qt.UserRole)
                if did:
                    self._download_row_map[did] = r

    @Slot(str, float, str)
    def on_download_progress(self, download_id: str, percent: float, status: str):
        """Handle download progress"""
        if download_id in self.downloads:
            dl = self.downloads[download_id]
            dl.progress = percent
            dl.status = status

            # O(1) table update via row map
            row = self._download_row_map.get(download_id)
            if row is not None:
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

            # Update main progress bar
            self.progress_bar.setValue(int(percent))
            self.status_label.setText(self.get_text('downloading', percent=percent))
            title = dl.title[:40]
            if status == "processing":
                if dl.format_type == "audio":
                    self.set_statusbar(f"Converting audio: {title}...")
                else:
                    self.set_statusbar(f"Merging video: {title}...")
            else:
                self.set_statusbar(f"Downloading: {title} - {percent:.0f}%")

    @Slot(str, str, str)
    def on_download_finished(self, download_id: str, status: str, filepath: str):
        """Handle download finished"""
        log.info(f"Download finished: {download_id}")

        if download_id in self.downloads:
            self.downloads[download_id].status = "done"
            self.downloads[download_id].filepath = filepath

            # O(1) table update via row map
            row = self._download_row_map.get(download_id)
            if row is not None:
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
                    play_btn.setText("\u25b6 Play")
                    play_btn.setProperty("btn_state", "idle")
                    play_btn.setStyleSheet("")
                    play_btn.setEnabled(True)

        # Clean up worker
        _worker = self.download_workers.pop(download_id, None)
        if _worker:
            _worker.deleteLater()

        # Re-enable download button
        self._reset_download_btn()
        self.progress_bar.setValue(100)
        self.status_label.setText(self.get_text('done'))
        QTimer.singleShot(2000, lambda: self.progress_bar.setValue(0))
        _dl = self.downloads.get(download_id)
        title = _dl.title[:50] if _dl else ""
        format_type = _dl.format_type if _dl else "video"
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
                title,
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
        log.error(f"Download error: {error}")

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

            # O(1) table update via row map
            row = self._download_row_map.get(download_id)
            if row is not None:
                status_item = self.downloads_table.item(row, 2)
                if status_item:
                    status_item.setText("Failed")
                    status_item.setForeground(QColor("#ff4444"))
                play_btn = self.downloads_table.cellWidget(row, 3)
                if play_btn:
                    play_btn.setText("\u25b6 Play")
                    play_btn.setProperty("btn_state", "idle")
                    play_btn.setStyleSheet("")
                    play_btn.setEnabled(False)

        # Clean up worker
        _worker = self.download_workers.pop(download_id, None)
        if _worker:
            _worker.deleteLater()

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
                log.info(f"Playing: {filepath}")

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
            log.info(f"Cancelled download: {download_id}")

        btn.setText("\u25b6 Play")
        btn.setProperty("btn_state", "idle")
        btn.setStyleSheet("")
        btn.setEnabled(False)

        row = self._download_row_map.get(download_id)
        if row is not None:
            status_item = self.downloads_table.item(row, 2)
            if status_item:
                status_item.setText("Cancelled")
                status_item.setForeground(QColor("#888888"))

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
                        btn.setText("\u23f9 Stop")
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

                        btn.setText("\u23f9 Stop")
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
            self.current_playing_btn.setText("\u25b6 Play")
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
            self.external_player_process = subprocess.Popen(
                [video_player, filepath],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            log.info(f"Playing video in {video_player}: {title}")
            self.now_playing_label.setText(f"{self.get_text('now_playing')} {title}")

            # Monitor external player so we reset button when it closes
            if self._ext_player_timer is None:
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
            if self._ext_player_timer is not None:
                self._ext_player_timer.stop()
            return

        retcode = self.external_player_process.poll()
        if retcode is not None:
            # Player has exited
            self.external_player_process = None
            if self._ext_player_timer is not None:
                self._ext_player_timer.stop()
            log.info("External player closed, resetting button state")
            # Reset the play button in downloads table
            if self.current_playing_btn:
                self.current_playing_btn.setText("\u25b6 Play")
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
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.error(f"Failed to save config: {e}")

    def seek_position(self, position):
        """Seek to position"""
        duration = self.media_player.duration()
        if duration > 0:
            new_pos = int(position * duration / 100)
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
        duration = self.media_player.duration()
        if not self.slider_is_pressed and duration > 0:
            percent = int(position * 100 / duration)
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
            self.current_playing_btn.setText("\u25b6 Play")
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

        if rows_to_remove:
            self._rebuild_row_map()

        if self.downloads_table.rowCount() == 0:
            self.downloads_table.hide()
            self.downloads_placeholder.show()

        log.info(f"Cleared {len(rows_to_remove)} completed downloads")

    def open_downloads_folder(self):
        """Open downloads folder"""
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_path))

    def _style_context_menu(self, menu: QMenu):
        """Apply stylesheet + palette to context menu for reliable highlighting on KDE/Plasma"""
        theme = get_theme(getattr(self, '_current_theme_id', 'dark'))
        if theme and "menu_style" in theme:
            menu.setStyleSheet(theme["menu_style"])
            palette = menu.palette()
            palette.setColor(QPalette.ColorRole.Highlight, QColor(theme["palette"].get("Highlight", "#00aa44")))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
            menu.setPalette(palette)

    def show_video_context_menu(self, pos):
        """Right-click context menu on search results list"""
        item = self.results_list.itemAt(pos)
        if not item:
            return
        widget = self.results_list.itemWidget(item)
        if not widget or not isinstance(widget, VideoItemWidget):
            return

        video = widget.video_data
        url = video.get('url') or ''
        if not url:
            video_id = video.get('id', '')
            if video_id:
                url = f"https://www.youtube.com/watch?v={video_id}"
        title = video.get('title', '')

        menu = QMenu(self)
        self._style_context_menu(menu)

        dl_action = menu.addAction('\u2b07\ufe0f  ' + self.get_text('download_btn'))
        dl_action.setEnabled(bool(url))
        dl_action.triggered.connect(lambda: self._ctx_download_video(video))

        menu.addSeparator()

        copy_url_action = menu.addAction('\U0001f517  ' + self.get_text('copy_url'))
        copy_url_action.setEnabled(bool(url))
        copy_url_action.triggered.connect(lambda: QApplication.clipboard().setText(url))

        copy_title_action = menu.addAction('\U0001f4cb  ' + self.get_text('copy_title'))
        copy_title_action.setEnabled(bool(title))
        copy_title_action.triggered.connect(lambda: QApplication.clipboard().setText(title))

        menu.addSeparator()

        open_action = menu.addAction('\U0001f310  ' + self.get_text('open_in_browser'))
        open_action.setEnabled(bool(url))
        open_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

        menu.exec(self.results_list.viewport().mapToGlobal(pos))

    def _ctx_download_video(self, video: dict):
        """Start download for a video from context menu"""
        self.selected_video = video
        self.do_download()

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
        self._style_context_menu(menu)

        file_exists = download.filepath and os.path.exists(download.filepath)
        is_done = download.status == 'done'

        # Play
        play_action = menu.addAction(f"\u25b6 {self.get_text('ctx_play')}")
        play_action.setEnabled(file_exists and is_done)
        play_action.triggered.connect(lambda: self._ctx_play(download_id, row))

        menu.addSeparator()

        # Open containing folder
        open_action = menu.addAction(f"\U0001f4c2 {self.get_text('ctx_open_folder')}")
        open_action.setEnabled(file_exists)
        open_action.triggered.connect(lambda: self._ctx_open_folder(download))

        # Download again
        again_action = menu.addAction(f"\u2b07 {self.get_text('ctx_download_again')}")
        again_action.setEnabled(bool(download.url))
        again_action.triggered.connect(lambda: self._ctx_download_again(download))

        menu.addSeparator()

        # Convert to submenu
        convert_menu = menu.addMenu(f"\U0001f504 {self.get_text('ctx_convert_to')}")
        self._style_context_menu(convert_menu)
        convert_menu.setEnabled(file_exists and is_done)
        for fmt in ['MP3', 'MP4', 'FLAC', 'WAV', 'OGG', 'AAC']:
            action = convert_menu.addAction(fmt)
            action.triggered.connect(lambda checked, f=fmt: self._ctx_convert(download, f))

        menu.addSeparator()

        # Remove from list
        remove_action = menu.addAction(f"\U0001f5d1 {self.get_text('ctx_remove')}")
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
        """Context menu: Download again - directly start a new download"""
        if not download.url:
            return

        new_download = DownloadItem(
            url=download.url,
            title=download.title,
            output_path=self.output_path,
            format_type=download.format_type,
            quality=download.quality
        )
        self.downloads[new_download.id] = new_download
        self.add_download_to_table(new_download)

        cookies_browser = self.settings.value("cookies_browser", "", type=str)
        embed_metadata = self.settings.value("embed_metadata", True, type=bool)
        speed_limit = self.settings.value("speed_limit", 0, type=int)
        worker = DownloadWorker(new_download, self.signals, cookies_browser, embed_metadata, speed_limit)
        self.download_workers[new_download.id] = worker
        worker.start()

        self.set_statusbar(f"Re-downloading: {new_download.title}")
        log.info(f"Re-download started: {new_download.title}")

    def _ctx_convert(self, download: DownloadItem, target_fmt: str):
        """Context menu: Convert file using FFmpeg (background process with QTimer polling)"""
        if not download.filepath or not os.path.exists(download.filepath):
            return

        # Stop any previous conversion timer/process
        if self._convert_timer is not None:
            self._convert_timer.stop()
            self._convert_timer = None
        if self._convert_proc is not None:
            try:
                self._convert_proc.terminate()
            except Exception:
                pass
            self._convert_proc = None

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
        log.info(f"Converting: {source} -> {dest}")

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
                    stderr = ""
                    try:
                        if proc.stderr:
                            stderr = proc.stderr.read().decode(errors='replace')[-200:]
                            proc.stderr.close()
                    except Exception:
                        pass
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
        self._rebuild_row_map()
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

            # Stop search worker if running
            if self.search_worker and self.search_worker.isRunning():
                self.search_worker.quit()
                self.search_worker.wait(300)

            # Stop external player monitor timer
            if self._ext_player_timer is not None:
                self._ext_player_timer.stop()

            # Stop conversion timer and process
            if self._convert_timer is not None:
                self._convert_timer.stop()
                self._convert_timer = None
            if self._convert_proc is not None:
                try:
                    self._convert_proc.terminate()
                except Exception:
                    pass
                self._convert_proc = None

            # Cancel any running download workers (snapshot values to avoid mutation during iteration)
            for worker in list(self.download_workers.values()):
                if worker.isRunning():
                    worker.cancel()

            # Clean up all preview temp dirs
            self._cleanup_all_preview_temps()

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
