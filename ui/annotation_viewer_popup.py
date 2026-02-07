"""
Annotation Viewer Popup - Read-only popup for viewing annotations.
Used when opening files with existing annotations (Reader Mode).
"""
import os
import logging
from typing import List, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QFrame, QWidget, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from ui.styles import default_theme

logger = logging.getLogger(__name__)


class ImageViewThumbnail(QFrame):
    """A read-only thumbnail widget for displaying an attached image."""
    
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.init_ui()
    
    def init_ui(self):
        """Initialize the thumbnail UI."""
        self.setFixedSize(80, 80)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {default_theme.card_background};
                border: 1px solid {default_theme.border_light};
                border-radius: 6px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        
        # Image label
        self.img_label = QLabel()
        self.img_label.setFixedSize(72, 72)
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("border: none;")
        
        # Load and scale image
        if os.path.exists(self.image_path):
            pixmap = QPixmap(self.image_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    72, 72,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.img_label.setPixmap(scaled)
            else:
                self.img_label.setText("❌")
        else:
            self.img_label.setText("❌")
        
        layout.addWidget(self.img_label)


class AnnotationViewerPopup(QDialog):
    """Read-only popup dialog for viewing an annotation."""
    
    def __init__(self, annotation_id: int, point: tuple, text: str = "", 
                 image_paths: Optional[List[str]] = None, parent=None):
        super().__init__(parent)
        self.annotation_id = annotation_id
        self.point = point
        self.text = text
        self.image_paths = image_paths or []
        
        self.setWindowTitle(f"View Annotation {annotation_id}")
        self.setModal(False)
        self.setMinimumSize(320, 300)
        self.setMaximumSize(400, 450)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the popup UI."""
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {default_theme.card_background};
                border: 1px solid {default_theme.border_standard};
                border-radius: 10px;
            }}
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Header with Reader Mode indicator
        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"📍 Point {self.annotation_id}")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(13)
        title_label.setFont(title_font)
        title_label.setStyleSheet(f"color: {default_theme.text_title};")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Reader mode badge
        reader_badge = QLabel("📖 View Only")
        reader_badge.setStyleSheet(f"""
            QLabel {{
                background-color: #DBEAFE;
                color: #1E40AF;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: bold;
            }}
        """)
        header_layout.addWidget(reader_badge)
        
        main_layout.addLayout(header_layout)
        
        # Coordinates
        coord_text = f"📐 ({self.point[0]:.2f}, {self.point[1]:.2f}, {self.point[2]:.2f})"
        coord_label = QLabel(coord_text)
        coord_label.setStyleSheet(f"color: {default_theme.text_secondary}; font-size: 10px;")
        main_layout.addWidget(coord_label)
        
        # Comment section
        if self.text:
            comment_label = QLabel("Comment:")
            comment_label.setStyleSheet(f"color: {default_theme.text_primary}; font-size: 11px; font-weight: bold;")
            main_layout.addWidget(comment_label)
            
            # Read-only text display
            text_display = QTextEdit()
            text_display.setPlainText(self.text)
            text_display.setReadOnly(True)
            text_display.setMinimumHeight(60)
            text_display.setMaximumHeight(100)
            text_display.setStyleSheet(f"""
                QTextEdit {{
                    background-color: {default_theme.row_bg_standard};
                    border: 1px solid {default_theme.border_light};
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 11px;
                    color: {default_theme.text_primary};
                }}
            """)
            main_layout.addWidget(text_display)
        else:
            no_comment = QLabel("No comment provided")
            no_comment.setStyleSheet(f"color: {default_theme.text_secondary}; font-size: 11px; font-style: italic;")
            main_layout.addWidget(no_comment)
        
        # Photos section
        if self.image_paths:
            photos_label = QLabel(f"Photos ({len(self.image_paths)}):")
            photos_label.setStyleSheet(f"color: {default_theme.text_primary}; font-size: 11px; font-weight: bold;")
            main_layout.addWidget(photos_label)
            
            # Photo thumbnails container
            photos_scroll = QScrollArea()
            photos_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            photos_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            photos_scroll.setWidgetResizable(True)
            photos_scroll.setFixedHeight(100)
            photos_scroll.setFrameShape(QFrame.NoFrame)
            photos_scroll.setStyleSheet("background: transparent;")
            
            photos_container = QWidget()
            photos_layout = QHBoxLayout(photos_container)
            photos_layout.setContentsMargins(0, 0, 0, 0)
            photos_layout.setSpacing(8)
            photos_layout.setAlignment(Qt.AlignLeft)
            
            for path in self.image_paths:
                thumb = ImageViewThumbnail(path)
                photos_layout.addWidget(thumb)
            
            photos_scroll.setWidget(photos_container)
            main_layout.addWidget(photos_scroll)
        
        main_layout.addStretch()
        
        # Close button only (no edit/delete in reader mode)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.setFixedHeight(36)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {default_theme.row_bg_standard};
                border: 1px solid {default_theme.border_light};
                border-radius: 6px;
                padding: 8px 24px;
                font-size: 12px;
                color: {default_theme.text_primary};
            }}
            QPushButton:hover {{
                background-color: {default_theme.row_bg_hover};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        main_layout.addLayout(btn_layout)
