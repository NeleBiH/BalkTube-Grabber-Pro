"""
Theme definitions for BalkGrab.

To create a new theme:
1. Use _make_stylesheet() with a color dict
2. Add it to the THEMES dict with a unique key
3. Add a translation key 'theme_<key>' in translations.py for each language

Each theme has:
  - "name": display name (used as fallback if no translation key exists)
  - "stylesheet": full Qt stylesheet string
  - "palette": dict of QPalette color roles -> hex colors
  - "menu_style": stylesheet for context menus (applied per-menu for KDE compatibility)
"""


def _make_stylesheet(c: dict) -> str:
    """Generate a full Qt stylesheet from a color dictionary.

    Required keys: bg, bg_alt, bg_deep, fg, fg_dim, accent, accent_dark,
                   border, highlight_bg, highlight_fg
    """
    return f"""
    QMainWindow, QWidget {{
        background-color: {c['bg']};
        color: {c['fg']};
    }}
    QTabWidget::pane {{
        border: 1px solid {c['border']};
        border-radius: 8px;
        background-color: {c['bg']};
    }}
    QTabBar::tab {{
        background-color: {c['bg_alt']};
        color: {c['fg_dim']};
        padding: 12px 24px;
        margin-right: 2px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-size: 13px;
    }}
    QTabBar::tab:selected {{
        background-color: {c['bg']};
        color: {c['accent']};
        font-weight: bold;
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {c['bg_deep']};
    }}
    QLineEdit {{
        background-color: {c['bg_alt']};
        border: 2px solid {c['border']};
        border-radius: 8px;
        padding: 10px;
        font-size: 14px;
        color: {c['fg']};
    }}
    QLineEdit:focus {{
        border: 2px solid {c['accent']};
    }}
    QPushButton {{
        background-color: {c['accent']};
        color: {c['accent_fg']};
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 14px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {c['accent_dark']};
    }}
    QPushButton:pressed {{
        background-color: {c['accent_darker']};
    }}
    QPushButton:disabled {{
        background-color: {c['bg_deep']};
        color: {c['fg_dim']};
    }}
    QPushButton#downloadBtn {{
        background-color: {c['accent']};
        color: {c['accent_fg']};
        font-size: 16px;
        font-weight: bold;
        padding: 15px 40px;
    }}
    QPushButton#downloadBtn:hover {{
        background-color: {c['accent_dark']};
    }}
    QPushButton#playBtn {{
        background-color: {c['accent']};
        font-size: 20px;
        padding: 10px 30px;
        min-width: 60px;
    }}
    QPushButton#stopBtn {{
        background-color: #ff4444;
        font-size: 16px;
        padding: 10px 20px;
    }}
    QPushButton#previewPlayBtn {{
        background-color: transparent;
        border: none;
        padding: 0px;
    }}
    QPushButton#previewPlayBtn:hover {{
        background-color: {c['accent']}30;
        border-radius: 4px;
    }}
    QPushButton#previewPlayBtn:disabled {{
        background-color: transparent;
        border: none;
    }}
    QPushButton#secondaryBtn {{
        background-color: {c['bg_deep']};
        color: {c['fg']};
        border: 2px solid {c['accent']};
    }}
    QPushButton#secondaryBtn:hover {{
        background-color: {c['border']};
        border: 2px solid {c['accent_dark']};
    }}
    QListWidget {{
        background-color: {c['bg_alt']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }}
    QListWidget::item {{
        background-color: {c['bg_deep']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        margin: 3px 2px;
        padding: 4px;
    }}
    QListWidget::item:selected {{
        background-color: {c['highlight_bg']};
        border: 1px solid {c['accent']};
    }}
    QListWidget::item:hover {{
        background-color: {c['border']};
        border: 1px solid {c['fg_dim']};
    }}
    QListWidget::item:hover:selected {{
        background-color: {c['highlight_bg']};
        border: 1px solid {c['accent']};
    }}
    QComboBox {{
        background-color: {c['bg_alt']};
        border: 2px solid {c['border']};
        border-radius: 8px;
        padding: 10px;
        font-size: 13px;
        min-width: 200px;
        color: {c['fg']};
    }}
    QComboBox:hover {{
        border: 2px solid {c['accent']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c['bg_alt']};
        border: 2px solid {c['border']};
        color: {c['fg']};
        selection-background-color: {c['accent']};
        selection-color: {c['accent_fg']};
        outline: none;
    }}
    QComboBox QAbstractItemView::item {{
        padding: 6px 10px;
        min-height: 24px;
        background-color: transparent;
    }}
    QComboBox QAbstractItemView::item:hover {{
        background-color: {c['highlight_bg']};
        color: {c['highlight_fg']};
    }}
    QComboBox QAbstractItemView::item:selected {{
        background-color: {c['accent']};
        color: {c['accent_fg']};
    }}
    QProgressBar {{
        background-color: {c['bg_alt']};
        border: none;
        border-radius: 8px;
        height: 20px;
        text-align: center;
        color: {c['accent_fg']};
        font-weight: bold;
    }}
    QProgressBar::chunk {{
        background-color: {c['accent']};
        border-radius: 8px;
    }}
    QGroupBox {{
        font-size: 14px;
        font-weight: bold;
        border: 2px solid {c['border']};
        border-radius: 10px;
        margin-top: 15px;
        padding-top: 15px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 10px;
    }}
    QRadioButton, QCheckBox {{
        font-size: 13px;
        spacing: 8px;
    }}
    QRadioButton::indicator, QCheckBox::indicator {{
        width: 18px;
        height: 18px;
    }}
    QRadioButton::indicator:checked, QCheckBox::indicator:checked {{
        background-color: {c['accent']};
        border: 2px solid {c['accent']};
        border-radius: 9px;
    }}
    QRadioButton::indicator:unchecked, QCheckBox::indicator:unchecked {{
        background-color: {c['bg_alt']};
        border: 2px solid {c['border']};
        border-radius: 9px;
    }}
    QCheckBox::indicator {{
        border-radius: 4px;
    }}
    QCheckBox::indicator:checked {{
        border-radius: 4px;
    }}
    QSlider::groove:horizontal {{
        background: {c['border']};
        height: 8px;
        border-radius: 4px;
    }}
    QSlider::handle:horizontal {{
        background: {c['accent']};
        width: 16px;
        height: 16px;
        margin: -4px 0;
        border-radius: 8px;
    }}
    QSlider::sub-page:horizontal {{
        background: {c['accent']};
        border-radius: 4px;
    }}
    QTableWidget {{
        background-color: {c['bg_alt']};
        border: 2px solid {c['border']};
        border-radius: 8px;
        gridline-color: {c['border']};
    }}
    QTableWidget::item {{
        padding: 8px;
    }}
    QTableWidget::item:selected {{
        background-color: {c['accent']};
        color: {c['accent_fg']};
    }}
    QHeaderView::section {{
        background-color: {c['bg_alt']};
        color: {c['accent']};
        padding: 10px;
        border: none;
        font-weight: bold;
    }}
    QTextEdit {{
        background-color: {c['bg_alt']};
        border: 2px solid {c['border']};
        border-radius: 8px;
        padding: 10px;
    }}
    QSpinBox {{
        background-color: {c['bg_alt']};
        border: 2px solid {c['border']};
        border-radius: 8px;
        padding: 8px;
        font-size: 13px;
    }}
    QSpinBox::up-button, QSpinBox::down-button {{
        background-color: {c['accent']};
        border: none;
        width: 20px;
    }}
    QSpinBox::up-button {{
        border-top-right-radius: 6px;
    }}
    QSpinBox::down-button {{
        border-bottom-right-radius: 6px;
    }}
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: {c['accent_dark']};
    }}
    QSpinBox::up-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-bottom: 6px solid white;
        width: 0;
        height: 0;
    }}
    QSpinBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid white;
        width: 0;
        height: 0;
    }}
    QScrollBar:vertical {{
        background-color: {c['bg_alt']};
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background-color: {c['accent']};
        border-radius: 6px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {c['accent_dark']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
        background: none;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: {c['bg_alt']};
    }}
    QScrollBar:horizontal {{
        background-color: {c['bg_alt']};
        height: 12px;
        border-radius: 6px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {c['accent']};
        border-radius: 6px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {c['accent_dark']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
        background: none;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: {c['bg_alt']};
    }}
    QMenu {{
        background-color: {c['bg_alt']};
        color: {c['fg']};
        border: 1px solid {c['border']};
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 20px;
    }}
    QMenu::item:selected {{
        background-color: {c['accent']};
        color: {c['accent_fg']};
    }}
    QMenu::item:disabled {{
        color: {c['fg_dim']};
    }}
    QMenu::separator {{
        height: 1px;
        background: {c['border']};
        margin: 4px 8px;
    }}
"""


def _make_menu_style(c: dict) -> str:
    """Generate a context menu stylesheet from a color dictionary."""
    return f"""
    QMenu {{ background-color: {c['bg_alt']}; color: {c['fg']}; border: 1px solid {c['border']}; padding: 4px; }}
    QMenu::item {{ padding: 6px 20px; }}
    QMenu::item:selected {{ background-color: {c['accent']}; color: {c['accent_fg']}; }}
    QMenu::item:disabled {{ color: {c['fg_dim']}; }}
    QMenu::separator {{ height: 1px; background: {c['border']}; margin: 4px 8px; }}
"""


# ---------------------------------------------------------------------------
# BalkGrab Dark — the default green-on-dark theme
# ---------------------------------------------------------------------------

_DARK = {
    'bg': '#1e1e1e', 'bg_alt': '#2d2d2d', 'bg_deep': '#3d3d3d',
    'fg': '#ffffff', 'fg_dim': '#888888',
    'accent': '#00ff88', 'accent_dark': '#00cc6a', 'accent_darker': '#009950',
    'accent_fg': '#1a1a1a',
    'border': '#3d3d3d',
    'highlight_bg': '#1a3d2a', 'highlight_fg': '#ffffff',
}

# ---------------------------------------------------------------------------
# Nord — arctic, north-bluish clean and elegant
# https://www.nordtheme.com
# ---------------------------------------------------------------------------

_NORD = {
    'bg': '#2e3440', 'bg_alt': '#3b4252', 'bg_deep': '#434c5e',
    'fg': '#eceff4', 'fg_dim': '#7b88a1',
    'accent': '#88c0d0', 'accent_dark': '#81a1c1', 'accent_darker': '#5e81ac',
    'accent_fg': '#2e3440',
    'border': '#4c566a',
    'highlight_bg': '#434c5e', 'highlight_fg': '#eceff4',
}

# ---------------------------------------------------------------------------
# Dracula — a dark theme for the 21st century
# https://draculatheme.com
# ---------------------------------------------------------------------------

_DRACULA = {
    'bg': '#282a36', 'bg_alt': '#343746', 'bg_deep': '#44475a',
    'fg': '#f8f8f2', 'fg_dim': '#6272a4',
    'accent': '#bd93f9', 'accent_dark': '#b380e8', 'accent_darker': '#9a5fd4',
    'accent_fg': '#282a36',
    'border': '#44475a',
    'highlight_bg': '#44475a', 'highlight_fg': '#f8f8f2',
}

# ---------------------------------------------------------------------------
# Catppuccin Mocha — Soothing pastel theme
# https://catppuccin.com
# ---------------------------------------------------------------------------

_CATPPUCCIN = {
    'bg': '#1e1e2e', 'bg_alt': '#313244', 'bg_deep': '#45475a',
    'fg': '#cdd6f4', 'fg_dim': '#6c7086',
    'accent': '#a6e3a1', 'accent_dark': '#94e2d5', 'accent_darker': '#74c7ec',
    'accent_fg': '#1e1e2e',
    'border': '#45475a',
    'highlight_bg': '#45475a', 'highlight_fg': '#cdd6f4',
}

# ---------------------------------------------------------------------------
# Gruvbox — retro groove color scheme
# https://github.com/morhetz/gruvbox
# ---------------------------------------------------------------------------

_GRUVBOX = {
    'bg': '#282828', 'bg_alt': '#3c3836', 'bg_deep': '#504945',
    'fg': '#ebdbb2', 'fg_dim': '#928374',
    'accent': '#fabd2f', 'accent_dark': '#fe8019', 'accent_darker': '#d3869b',
    'accent_fg': '#282828',
    'border': '#504945',
    'highlight_bg': '#504945', 'highlight_fg': '#ebdbb2',
}

# ---------------------------------------------------------------------------
# Arc-Dark — a flat theme with transparent elements (dark variant)
# https://github.com/LinxGem33/Arc-Dark
# ---------------------------------------------------------------------------

_ARC_DARK = {
    'bg': '#383c4a', 'bg_alt': '#404552', 'bg_deep': '#4b5064',
    'fg': '#d3dae3', 'fg_dim': '#6c7a89',
    'accent': '#5294e2', 'accent_dark': '#4182c4', 'accent_darker': '#3670a8',
    'accent_fg': '#ffffff',
    'border': '#4b5064',
    'highlight_bg': '#4182c4', 'highlight_fg': '#ffffff',
}

# ---------------------------------------------------------------------------
# Tokyo Night — a clean, dark VS Code inspired theme
# https://github.com/enkia/tokyo-night-vscode-theme
# ---------------------------------------------------------------------------

_TOKYO_NIGHT = {
    'bg': '#1a1b26', 'bg_alt': '#24283b', 'bg_deep': '#414868',
    'fg': '#c0caf5', 'fg_dim': '#565f89',
    'accent': '#7aa2f7', 'accent_dark': '#2ac3de', 'accent_darker': '#bb9af7',
    'accent_fg': '#1a1b26',
    'border': '#414868',
    'highlight_bg': '#414868', 'highlight_fg': '#c0caf5',
}


def _build_theme(name: str, colors: dict) -> dict:
    return {
        "name": name,
        "stylesheet": _make_stylesheet(colors),
        "menu_style": _make_menu_style(colors),
        "palette": {
            "Highlight": colors['accent'],
            "HighlightedText": colors['accent_fg'],
            "Window": colors['bg'],
            "WindowText": colors['fg'],
            "Base": colors['bg_alt'],
            "Text": colors['fg'],
        },
    }


# ---------------------------------------------------------------------------
# Theme registry
# ---------------------------------------------------------------------------

THEMES = {
    "dark": _build_theme("BalkGrab Dark", _DARK),
    "nord": _build_theme("Nord", _NORD),
    "dracula": _build_theme("Dracula", _DRACULA),
    "catppuccin": _build_theme("Catppuccin Mocha", _CATPPUCCIN),
    "gruvbox": _build_theme("Gruvbox", _GRUVBOX),
    "arc_dark": _build_theme("Arc Dark", _ARC_DARK),
    "tokyo_night": _build_theme("Tokyo Night", _TOKYO_NIGHT),
}


def get_theme(theme_id: str) -> dict | None:
    """Get a theme by its ID. Returns None for 'system' (no custom theme)."""
    if theme_id == "system":
        return None
    return THEMES.get(theme_id)


def get_available_themes() -> list[tuple[str, str]]:
    """Return list of (theme_id, display_name) for all available themes.
    Always includes 'system' as the first option."""
    result = [("system", "System Default")]
    for tid, theme in THEMES.items():
        result.append((tid, theme["name"]))
    return result
