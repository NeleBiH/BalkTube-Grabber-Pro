"""Reusable Qt widgets."""

from PySide6.QtWidgets import QSlider, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QCheckBox
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap


class ClickableSlider(QSlider):
    """Slider that responds to clicks at the clicked position"""

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.sliderPressed.emit()
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
            self.sliderReleased.emit()
        super().mouseReleaseEvent(event)


class VideoItemWidget(QWidget):
    """Custom widget for displaying a video search result"""

    def __init__(self, video_data: dict, parent=None):
        super().__init__(parent)
        self.video_data = video_data
        self._setup_ui()

    def _setup_ui(self):
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

        meta_label = QLabel(f"{channel}  |  {duration_str}")
        meta_label.setStyleSheet("color: #aaaaaa; font-size: 11px;")
        info_layout.addWidget(meta_label)

        views = self.video_data.get('view_count', 0)
        if views:
            if views >= 1000000:
                views_str = f"{views / 1000000:.1f}M"
            elif views >= 1000:
                views_str = f"{views / 1000:.1f}K"
            else:
                views_str = str(views)
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
