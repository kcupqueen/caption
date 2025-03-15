import sys
from PyQt5.QtWidgets import QApplication, QTextEdit, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QSlider, QLabel, QSizeGrip, QMainWindow, QFrame
from PyQt5.QtGui import QTextCursor, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QPoint, QEvent, pyqtSignal, QSize
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings


class TitleBar(QFrame):
    """自定义标题栏"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.window = parent
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(0)
        
        # Title label
        self.title_label = QLabel("翻译")
        self.title_label.setStyleSheet("color: #333; font-size: 13px;")
        layout.addWidget(self.title_label)
        layout.addStretch()
        
        # Window controls
        btn_size = 46
        btn_style = """
            QPushButton {
                border: none;
                padding: 0;
                background: transparent;
            }
            QPushButton:hover {
                background-color: rgba(0, 0, 0, 0.1);
            }
            #close_button:hover {
                background-color: #e81123;
                color: white;
            }
        """
        
        self.minimize_btn = QPushButton("─")
        self.minimize_btn.setFixedSize(btn_size, self.height())
        self.minimize_btn.clicked.connect(self.window.showMinimized)
        
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFixedSize(btn_size, self.height())
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("close_button")
        self.close_btn.setFixedSize(btn_size, self.height())
        self.close_btn.clicked.connect(self.window.hide_window)  # Use the new hide_window method
        
        for btn in (self.minimize_btn, self.maximize_btn, self.close_btn):
            btn.setStyleSheet(btn_style)
            layout.addWidget(btn)
            
        self.setStyleSheet("""
            TitleBar {
                background: #f0f0f0;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
        """)
        
    def toggle_maximize(self):
        if self.window.isMaximized():
            self.window.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.window.showMaximized()
            self.maximize_btn.setText("❐")
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.window.dragging = True
            self.window.offset = event.pos()
            
    def mouseMoveEvent(self, event):
        if self.window.dragging and self.window.offset:
            self.window.move(self.window.mapToParent(event.pos() - self.window.offset))
            
    def mouseReleaseEvent(self, event):
        self.window.dragging = False


class FloatingTranslation(QMainWindow):
    """悬浮翻译窗口"""
    windowClosed = pyqtSignal(dict)
    captionReady = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add custom title bar
        self.title_bar = TitleBar(self)
        layout.addWidget(self.title_bar)
        
        # Content widget with border
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Translation content
        self.label = QWebEngineView()
        self.label.setMinimumSize(300, 200)
        self.label.settings().setAttribute(QWebEngineSettings.ShowScrollBars, True)
        self.zoom_factor = 1.0
        
        # Bottom controls
        bottom_layout = QHBoxLayout()
        self.save_button = QPushButton("⭐ 收藏")
        self.save_button.clicked.connect(self.save_translation)
        bottom_layout.addWidget(self.save_button)
        bottom_layout.addStretch()
        
        # Add widgets to content layout
        content_layout.addWidget(self.label)
        content_layout.addLayout(bottom_layout)
        
        # Add content widget to main layout
        layout.addWidget(self.content_widget)
        
        # Styling
        self.setStyleSheet("""
            QMainWindow {
                background: white;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QPushButton {
                padding: 5px;
                margin: 2px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        # Window state
        self.dragging = False
        self.offset = None
        
        # Initial size
        self.resize(400, 300)
        
        # Monitor global mouse events
        QApplication.instance().installEventFilter(self)
        
    def hide_window(self):
        """Hide the window and emit the windowClosed signal"""
        self.hide()
        self.windowClosed.emit({})
        
    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.adjust_zoom(0.1)
            else:
                self.adjust_zoom(-0.1)
            event.accept()
        else:
            super().wheelEvent(event)
            
    def adjust_zoom(self, delta):
        new_zoom = max(0.5, min(2.0, self.zoom_factor + delta))
        if new_zoom != self.zoom_factor:
            self.zoom_factor = new_zoom
            self.label.setZoomFactor(self.zoom_factor)

    def set_translation(self, text, pos, state):
        if state == "loaded":
            self.label.setHtml(text)
        else:
            print("not loaded")
            self.label.setHtml(text)
        self.move(pos)
        self.show()
        self.activateWindow()

    def save_translation(self):
        self.label.page().toHtml(lambda html: print("已收藏:", html))

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if not self.geometry().contains(event.globalPos()):
                self.hide_window()  # Use the new hide_window method
                return True
        return super().eventFilter(obj, event)


class TranslatorApp(QWidget):
    """主界面"""

    def __init__(self):
        super().__init__()

        self.textEdit = QTextEdit()
        self.textEdit.setText("Select any text to translate.")
        self.textEdit.mouseReleaseEvent = self.show_translation

        layout = QVBoxLayout()
        layout.addWidget(self.textEdit)
        self.setLayout(layout)

    def show_translation(self, event):
        """选中文字后创建新的 FloatingTranslation 窗口"""
        cursor = self.textEdit.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor_rect = self.textEdit.cursorRect(cursor)
            pos = self.textEdit.mapToGlobal(cursor_rect.bottomRight())

            floating_window = FloatingTranslation(self)  # 创建新窗口
            floating_window.set_translation(selected_text, pos)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslatorApp()
    window.resize(500, 300)
    window.show()
    sys.exit(app.exec_())
