"""All UI translations: English, Deutsch, Hrvatski/Srpski."""

TRANSLATIONS = {
    'en': {
        'app_title': 'BalkGrab',
        'tab_search': 'Search',
        'tab_downloads': 'Downloads',
        'tab_settings': 'Settings',
        'tab_about': 'About',
        'search_placeholder': 'Search YouTube or paste URL...',
        'search_btn': 'Search',
        'searching': 'Searching...',
        'results': 'Search Results',
        'preview': 'Preview',
        'select_video': 'Select video from list',
        'no_video_selected': 'No video selected',
        'format': 'Format',
        'video': 'Video',
        'audio': 'Audio',
        'quality': 'Quality:',
        'status': 'Status',
        'waiting': 'Waiting for selection...',
        'download_btn': 'DOWNLOAD NOW!',
        'stop_download': 'STOP DOWNLOAD',
        'found_videos': 'Found {count} videos!',
        'load_more': 'Load More Results',
        'no_results': 'No results',
        'ready_download': 'Ready to download!',
        'downloading': 'Downloading... {percent:.1f}%',
        'processing': 'Processing...',
        'done': 'Done!',
        'error': 'Error!',
        'output_folder': 'Output Folder',
        'browse': 'Browse...',
        'best_quality': 'Best quality',
        'downloads_title': 'Download Manager',
        'no_downloads': 'No downloads yet.\nSearch and download some music!',
        'filename': 'Filename',
        'progress': 'Progress',
        'status_col': 'Status',
        'actions': 'Actions',
        'clear_completed': 'Clear Completed',
        'open_folder': 'Open Folder',
        'ctx_play': 'Play',
        'ctx_open_folder': 'Open containing folder',
        'ctx_download_again': 'Download again',
        'ctx_convert_to': 'Convert to',
        'ctx_remove': 'Remove from list',
        'converting_file': 'Converting to {fmt}...',
        'conversion_done': 'Converted to {fmt} — check download folder',
        'conversion_failed': 'Conversion failed: {error}',
        'player_title': 'Media Player',
        'now_playing': 'Now Playing:',
        'nothing_playing': 'Nothing playing',
        'settings_title': 'Settings',
        'language': 'Language:',
        'appearance': 'Appearance',
        'theme': 'Theme:',
        'theme_system': 'System Default',
        'theme_dark': 'BalkGrab Dark',
        'theme_nord': 'Nord',
        'theme_dracula': 'Dracula',
        'theme_catppuccin': 'Catppuccin Mocha',
        'theme_gruvbox': 'Gruvbox',
        'theme_arc_dark': 'Arc Dark',
        'theme_tokyo_night': 'Tokyo Night',
        'system_tray': 'Show system tray icon',
        'minimize_tray': 'Minimize to system tray',
        'start_minimized': 'Start minimized',
        'continue_playing_tray': 'Continue playing when minimized to tray',
        'notifications': 'Show download notifications',
        'clipboard_monitor': 'Auto-detect YouTube/video URLs from clipboard',
        'downloads_settings': 'Downloads',
        'simultaneous': 'Simultaneous downloads:',
        'speed_limit': 'Download speed limit:',
        'speed_limit_unit': 'KB/s (0 = unlimited)',
        'embed_metadata': 'Embed metadata & cover art in audio files',
        'open_in_browser': 'Open in browser',
        'copy_url': 'Copy URL',
        'copy_title': 'Copy title',
        'download_location': 'Download location:',
        'about_title': 'About BalkGrab',
        'about_description': '''
<h3>What is this?</h3>
<p>BalkGrab is a free, open-source YouTube downloader.
Download videos in various resolutions or convert them to audio formats like MP3, FLAC, and more!</p>

<h3>Features</h3>
<ul>
<li>Search YouTube directly from the app</li>
<li>Preview videos with built-in stream player</li>
<li>Download videos in resolutions from 240p to 4K</li>
<li>Convert to audio: MP3, AAC, FLAC, WAV, OGG</li>
<li>Convert between video formats (MP4, MKV, AVI, WebM)</li>
<li>Concurrent download manager with progress tracking</li>
<li>Built-in media player for downloaded files</li>
<li>External video player support (VLC, MPV, etc.)</li>
<li>Embed metadata and thumbnails in downloads</li>
<li>Smart playlist detection with batch download</li>
<li>Clipboard auto-detection of YouTube URLs</li>
<li>Browser cookies support for age-restricted videos</li>
<li>7 built-in themes: Dark, Nord, Dracula, Catppuccin, Gruvbox, Arc Dark, Tokyo Night</li>
<li>Multi-language: English, Deutsch, Hrvatski/Srpski</li>
<li>System tray integration</li>
</ul>

<h3>Special Thanks</h3>
<table width="100%">
<tr><td><b>PySide6</b> — Qt for Python</td><td align="right"><a href="https://www.qt.io/qt-for-python">qt.io</a></td></tr>
<tr><td><b>yt-dlp</b> — Video downloader</td><td align="right"><a href="https://github.com/yt-dlp/yt-dlp">github.com/yt-dlp</a></td></tr>
<tr><td><b>FFmpeg</b> — Audio/Video processing</td><td align="right"><a href="https://ffmpeg.org">ffmpeg.org</a></td></tr>
<tr><td><b>Deno</b> — JavaScript runtime</td><td align="right"><a href="https://deno.land">deno.land</a></td></tr>
</table>
''',
        'license_title': 'License',
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
        'links_title': 'Links',
        'github': 'GitHub Repository',
        'report_bug': 'Report a Bug',
        'playlist_detected': 'Playlist Detected',
        'playlist_msg': 'This playlist contains {count} videos.\nWhat would you like to do?',
        'playlist_first_video': 'Show First Video',
        'playlist_load_first': 'First {count} videos',
        'playlist_load_all': 'All {count} videos',
        'playlist_load_btn': 'Load Playlist',
        'playlist_loading': 'Loading playlist info...',
        'playlist_warning': 'Loading many videos may be slow!',
        'playlist_cancel': 'Cancel',
        'footer': 'Made with Claude Code and some coffee | Balkan Edition'
    },
    'de': {
        'app_title': 'BalkGrab',
        'tab_search': 'Suchen',
        'tab_downloads': 'Downloads',
        'tab_settings': 'Einstellungen',
        'tab_about': 'Über',
        'search_placeholder': 'YouTube durchsuchen oder URL einfügen...',
        'search_btn': 'Suchen',
        'searching': 'Suche...',
        'results': 'Suchergebnisse',
        'preview': 'Vorschau',
        'select_video': 'Video aus Liste auswählen',
        'no_video_selected': 'Kein Video ausgewählt',
        'format': 'Format',
        'video': 'Video',
        'audio': 'Audio',
        'quality': 'Qualität:',
        'status': 'Status',
        'waiting': 'Warte auf Auswahl...',
        'download_btn': 'JETZT HERUNTERLADEN!',
        'stop_download': 'DOWNLOAD STOPPEN',
        'found_videos': '{count} Videos gefunden!',
        'load_more': 'Mehr Ergebnisse laden',
        'no_results': 'Keine Ergebnisse',
        'ready_download': 'Bereit zum Download!',
        'downloading': 'Herunterladen... {percent:.1f}%',
        'processing': 'Verarbeitung...',
        'done': 'Fertig!',
        'error': 'Fehler!',
        'output_folder': 'Ausgabeordner',
        'browse': 'Durchsuchen...',
        'best_quality': 'Beste Qualität',
        'downloads_title': 'Download-Manager',
        'no_downloads': 'Noch keine Downloads.\nSuche und lade Musik herunter!',
        'filename': 'Dateiname',
        'progress': 'Fortschritt',
        'status_col': 'Status',
        'actions': 'Aktionen',
        'clear_completed': 'Abgeschlossene löschen',
        'open_folder': 'Ordner öffnen',
        'ctx_play': 'Abspielen',
        'ctx_open_folder': 'Ordner öffnen',
        'ctx_download_again': 'Erneut herunterladen',
        'ctx_convert_to': 'Konvertieren zu',
        'ctx_remove': 'Aus Liste entfernen',
        'converting_file': 'Konvertiere zu {fmt}...',
        'conversion_done': 'Zu {fmt} konvertiert — im Download-Ordner prüfen',
        'conversion_failed': 'Konvertierung fehlgeschlagen: {error}',
        'player_title': 'Mediaplayer',
        'now_playing': 'Wird abgespielt:',
        'nothing_playing': 'Nichts wird abgespielt',
        'settings_title': 'Einstellungen',
        'language': 'Sprache:',
        'appearance': 'Aussehen',
        'theme': 'Thema:',
        'theme_system': 'Systemstandard',
        'theme_dark': 'BalkGrab Dark',
        'theme_nord': 'Nord',
        'theme_dracula': 'Dracula',
        'theme_catppuccin': 'Catppuccin Mocha',
        'theme_gruvbox': 'Gruvbox',
        'theme_arc_dark': 'Arc Dark',
        'theme_tokyo_night': 'Tokyo Night',
        'system_tray': 'Taskleistensymbol anzeigen',
        'minimize_tray': 'In Taskleiste minimieren',
        'start_minimized': 'Minimiert starten',
        'continue_playing_tray': 'Weiterspielen wenn in Taskleiste minimiert',
        'notifications': 'Download-Benachrichtigungen anzeigen',
        'clipboard_monitor': 'YouTube/Video-URLs aus Zwischenablage erkennen',
        'downloads_settings': 'Downloads',
        'simultaneous': 'Gleichzeitige Downloads:',
        'speed_limit': 'Download-Geschwindigkeitslimit:',
        'speed_limit_unit': 'KB/s (0 = unbegrenzt)',
        'embed_metadata': 'Metadaten & Cover-Art in Audiodateien einbetten',
        'open_in_browser': 'Im Browser öffnen',
        'copy_url': 'URL kopieren',
        'copy_title': 'Titel kopieren',
        'download_location': 'Download-Speicherort:',
        'about_title': 'Über BalkGrab',
        'about_description': '''
<h3>Was ist das?</h3>
<p>BalkGrab ist ein kostenloser, Open-Source YouTube-Downloader.
Laden Sie Videos in verschiedenen Auflösungen herunter oder konvertieren Sie sie in Audioformate wie MP3, FLAC und mehr!</p>

<h3>Funktionen</h3>
<ul>
<li>YouTube direkt in der App durchsuchen</li>
<li>Videos mit integriertem Stream-Player ansehen</li>
<li>Videos in Auflösungen von 240p bis 4K herunterladen</li>
<li>In Audio konvertieren: MP3, AAC, FLAC, WAV, OGG</li>
<li>Zwischen Videoformaten konvertieren (MP4, MKV, AVI, WebM)</li>
<li>Download-Manager mit parallelen Downloads und Fortschrittsverfolgung</li>
<li>Integrierter Mediaplayer für heruntergeladene Dateien</li>
<li>Externer Video-Player Support (VLC, MPV, usw.)</li>
<li>Metadaten und Thumbnails in Downloads einbetten</li>
<li>Intelligente Playlist-Erkennung mit Batch-Download</li>
<li>Automatische Erkennung von YouTube-URLs in der Zwischenablage</li>
<li>Browser-Cookies für altersbeschränkte Videos</li>
<li>7 integrierte Themes: Dark, Nord, Dracula, Catppuccin, Gruvbox, Arc Dark, Tokyo Night</li>
<li>Mehrsprachig: English, Deutsch, Hrvatski/Srpski</li>
<li>Taskleisten-Integration</li>
</ul>

<h3>Special Thanks</h3>
<table width="100%">
<tr><td><b>PySide6</b> — Qt für Python</td><td align="right"><a href="https://www.qt.io/qt-for-python">qt.io</a></td></tr>
<tr><td><b>yt-dlp</b> — Video-Downloader</td><td align="right"><a href="https://github.com/yt-dlp/yt-dlp">github.com/yt-dlp</a></td></tr>
<tr><td><b>FFmpeg</b> — Audio/Video-Verarbeitung</td><td align="right"><a href="https://ffmpeg.org">ffmpeg.org</a></td></tr>
<tr><td><b>Deno</b> — JavaScript-Laufzeitumgebung</td><td align="right"><a href="https://deno.land">deno.land</a></td></tr>
</table>
''',
        'license_title': 'Lizenz',
        'links_title': 'Links',
        'github': 'GitHub Repository',
        'report_bug': 'Fehler melden',
        'playlist_detected': 'Playlist erkannt',
        'playlist_msg': 'Diese Playlist enthält {count} Videos.\nWas möchten Sie tun?',
        'playlist_first_video': 'Erstes Video anzeigen',
        'playlist_load_first': 'Erste {count} Videos',
        'playlist_load_all': 'Alle {count} Videos',
        'playlist_load_btn': 'Playlist laden',
        'playlist_loading': 'Lade Playlist-Info...',
        'playlist_warning': 'Viele Videos zu laden kann langsam sein!',
        'playlist_cancel': 'Abbrechen',
        'footer': 'Mit Liebe und etwas Ćevapi gemacht | Balkan Edition'
    },
    'hr': {
        'app_title': 'BalkGrab',
        'tab_search': 'Traži',
        'tab_downloads': 'Preuzimanja',
        'tab_settings': 'Postavke',
        'tab_about': 'O aplikaciji',
        'search_placeholder': 'Pretraži YouTube ili zalijepi URL...',
        'search_btn': 'Pretraži',
        'searching': 'Tražim...',
        'results': 'Rezultati pretrage',
        'preview': 'Preview',
        'select_video': 'Odaberi video iz liste',
        'no_video_selected': 'Nije odabran video',
        'format': 'Format',
        'video': 'Video',
        'audio': 'Audio',
        'quality': 'Kvaliteta:',
        'status': 'Status',
        'waiting': 'Čekam da odabereš...',
        'download_btn': 'SKINI ODMAH!',
        'stop_download': 'ZAUSTAVI SKIDANJE',
        'found_videos': 'Pronađeno {count} videa!',
        'load_more': 'Učitaj više rezultata',
        'no_results': 'Nema rezultata',
        'ready_download': 'Spremno za skidanje!',
        'downloading': 'Skidam... {percent:.1f}%',
        'processing': 'Obrađujem...',
        'done': 'Gotovo!',
        'error': 'Greška!',
        'output_folder': 'Izlazna mapa',
        'browse': 'Odaberi...',
        'best_quality': 'Najbolja kvaliteta',
        'downloads_title': 'Upravitelj preuzimanja',
        'no_downloads': 'Nema preuzimanja.\nPretraži i skini neku muziku!',
        'filename': 'Naziv datoteke',
        'progress': 'Napredak',
        'status_col': 'Status',
        'actions': 'Akcije',
        'clear_completed': 'Očisti završene',
        'open_folder': 'Otvori mapu',
        'ctx_play': 'Pusti',
        'ctx_open_folder': 'Otvori mapu',
        'ctx_download_again': 'Skini ponovo',
        'ctx_convert_to': 'Konvertiraj u',
        'ctx_remove': 'Ukloni s liste',
        'converting_file': 'Konvertiranje u {fmt}...',
        'conversion_done': 'Konvertirano u {fmt} — provjeri mapu preuzimanja',
        'conversion_failed': 'Konverzija neuspješna: {error}',
        'player_title': 'Media Player',
        'now_playing': 'Sad svira:',
        'nothing_playing': 'Ništa ne svira',
        'settings_title': 'Postavke',
        'language': 'Jezik:',
        'appearance': 'Izgled',
        'theme': 'Tema:',
        'theme_system': 'Sistemska',
        'theme_dark': 'BalkGrab Dark',
        'theme_nord': 'Nord',
        'theme_dracula': 'Dracula',
        'theme_catppuccin': 'Catppuccin Mocha',
        'theme_gruvbox': 'Gruvbox',
        'theme_arc_dark': 'Arc Dark',
        'theme_tokyo_night': 'Tokyo Night',
        'system_tray': 'Prikaži ikonu u system trayu',
        'minimize_tray': 'Minimiziraj u system tray',
        'start_minimized': 'Pokreni minimizirano',
        'continue_playing_tray': 'Nastavi reprodukciju kad je minimizirano u tray',
        'notifications': 'Prikaži obavijesti o preuzimanju',
        'clipboard_monitor': 'Automatski detektuj YouTube/video URL-ove iz clipboarda',
        'downloads_settings': 'Preuzimanja',
        'simultaneous': 'Istovremena preuzimanja:',
        'speed_limit': 'Ograničenje brzine preuzimanja:',
        'speed_limit_unit': 'KB/s (0 = neograničeno)',
        'embed_metadata': 'Ugradi metapodatke i naslovnicu u audio datoteke',
        'open_in_browser': 'Otvori u pregledniku',
        'copy_url': 'Kopiraj URL',
        'copy_title': 'Kopiraj naslov',
        'download_location': 'Lokacija preuzimanja:',
        'about_title': 'O aplikaciji BalkGrab',
        'about_description': '''
<h3>Šta je ovo?</h3>
<p>BalkGrab je besplatan YouTube downloader otvorenog koda.
Skidaj videe u raznim rezolucijama ili ih pretvori u audio formate kao MP3, FLAC i druge!</p>

<h3>Mogućnosti</h3>
<ul>
<li>Pretraži YouTube direktno iz aplikacije</li>
<li>Pregledaj video sa ugrađenim stream playerom</li>
<li>Skidaj videe u rezolucijama od 240p do 4K</li>
<li>Pretvori u audio: MP3, AAC, FLAC, WAV, OGG</li>
<li>Pretvori između video formata (MP4, MKV, AVI, WebM)</li>
<li>Upravitelj preuzimanja sa paralelnim downloadima i praćenjem napretka</li>
<li>Ugrađeni media player za skinute fajlove</li>
<li>Podrška za eksterni video player (VLC, MPV, itd.)</li>
<li>Ugradnja metapodataka i thumbnaila u preuzimanja</li>
<li>Pametna detekcija playlisti sa batch downloadom</li>
<li>Auto-detekcija YouTube linkova iz clipboarda</li>
<li>Browser cookies podrška za age-restricted videe</li>
<li>7 ugrađenih tema: Dark, Nord, Dracula, Catppuccin, Gruvbox, Arc Dark, Tokyo Night</li>
<li>Višejezično: English, Deutsch, Hrvatski/Srpski</li>
<li>System tray integracija</li>
</ul>

<h3>Special Thanks</h3>
<table width="100%">
<tr><td><b>PySide6</b> — Qt za Python</td><td align="right"><a href="https://www.qt.io/qt-for-python">qt.io</a></td></tr>
<tr><td><b>yt-dlp</b> — Video downloader</td><td align="right"><a href="https://github.com/yt-dlp/yt-dlp">github.com/yt-dlp</a></td></tr>
<tr><td><b>FFmpeg</b> — Obrada audio/video zapisa</td><td align="right"><a href="https://ffmpeg.org">ffmpeg.org</a></td></tr>
<tr><td><b>Deno</b> — JavaScript okruženje</td><td align="right"><a href="https://deno.land">deno.land</a></td></tr>
</table>
''',
        'license_title': 'Licenca',
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
        'links_title': 'Linkovi',
        'github': 'GitHub Repozitorij',
        'report_bug': 'Prijavi grešku',
        'playlist_detected': 'Playlist detektovan',
        'playlist_msg': 'Ova playlista sadrži {count} videa.\nŠta želiš uraditi?',
        'playlist_first_video': 'Prikaži prvi video',
        'playlist_load_first': 'Prvih {count} videa',
        'playlist_load_all': 'Svih {count} videa',
        'playlist_load_btn': 'Učitaj playlistu',
        'playlist_loading': 'Učitavam info o playlisti...',
        'playlist_warning': 'Učitavanje puno videa može biti sporo!',
        'playlist_cancel': 'Odustani',
        'footer': 'Napravljeno s Claude Code i malo kave | Balkan Edition'
    }
}
