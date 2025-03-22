import sys
from PyQt5.QtWidgets import QApplication, QTextEdit, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QSlider, QLabel, QSizeGrip, QMainWindow, QFrame
from PyQt5.QtGui import QTextCursor, QPalette, QColor, QIcon, QPainter, QPolygon
from PyQt5.QtCore import Qt, QPoint, QEvent, pyqtSignal, QSize, QDir, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from functools import partial
from pathlib import Path

from caption import LookupState, LookUpType
from widget.ani_button import GifButton
from widget.thread_pool import GLOBAL_THREAD_POOL, Worker

html_content = """
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    padding: 10px;
                }}
                .text-preview {{
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 10px;
                    margin-bottom: 10px;
                    max-height: 150px;
                    overflow-y: auto;
                    white-space: pre-wrap;
                    word-break: break-word;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h3>Translate this text?</h3>
                <div class="text-preview">{}</div>
            </div>
        </body>
        </html>
        """

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

class TriangleSizeGrip(QSizeGrip):
    def __init__(self, parent=None):
        super(TriangleSizeGrip, self).__init__(parent)
        self.setFixedSize(16, 16)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # set the color and transparency, green
        green = QColor(0, 255, 0, 150)

        # 创建三角形
        triangle = QPolygon([
            QPoint(0, 16),  # 左下角
            QPoint(16, 16),  # 右下角
            QPoint(16, 0)  # 右上角
        ])

        # 填充三角形
        painter.setBrush(green)
        painter.setPen(Qt.NoPen)  # 无边框
        painter.drawPolygon(triangle)

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
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setObjectName("close_button")
        self.close_btn.setFixedSize(btn_size, self.height())
        self.close_btn.clicked.connect(self.window.hide_window)  # Use the new hide_window method
        
        for btn in [self.close_btn]:
            btn.setStyleSheet(btn_style)
            layout.addWidget(btn)
            
        self.setStyleSheet("""
            TitleBar {
                background: #f0f0f0;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
        """)
        
            
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

    def __init__(self, parent=None, online_func=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.online_func = online_func
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
        
        # Add QSizeGrip for resizing
        self.size_grip = TriangleSizeGrip(self)
        bottom_layout.addWidget(self.size_grip, 0, Qt.AlignRight | Qt.AlignBottom)
        self.confirm_button = GifButton("translate", str(ASSETS_DIR / "loading.gif"))
        # Add button to the bottom layout
        self.content_widget.layout().itemAt(1).layout().insertWidget(0, self.confirm_button)

        self.setStyleSheet(f"""
            QMainWindow {{
                background: white;
                border: 1px solid #ccc;
                border-radius: 5px;
            }}
            QPushButton {{
                padding: 5px;
                margin: 2px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                background-color: #e0e0e0;
            }}
        """)

        # Window state
        self.dragging = False
        self.offset = None
        
        # Initial size
        self.resize(400, 300)
        self.captionReady.connect(self.display_translation)

        # Monitor global mouse events
        #QApplication.instance().installEventFilter(self)

    def display_translation(self, event=None):
        pos = event['pos']
        state = event['state']
        text = event['text']
        lookup_type = event.get('lookup_type', LookUpType.WORD)
        print("display_translation, type is", lookup_type)
        if text:
            self.set_translation(text, pos, state)
        if lookup_type == LookUpType.SENTENCE and state == LookupState.LOADED:
            self.confirm_button.hide()
            self.save_button.show()
        if lookup_type == LookUpType.WORD:
            self.confirm_button.hide()
            self.save_button.show()

    def hide_window(self):
        """Hide the window and emit the windowClosed signal"""
        print("FloatingTranslation hide_window")
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

        if state == LookupState.LOADED:
            self.label.setHtml(text)
        elif state == LookupState.LOADING:
            self.label.setHtml(text)
        elif state == LookupState.CONFIRM:
            self.display_confirm_window(text, pos)
        else:
            pass
        new_pos = QPoint(pos.x(), pos.y() - self.height())
        self.move(new_pos)
        self.show()
        self.activateWindow()

    def display_confirm_window(self, text, pos):
        """Display a confirmation window asking if user wants to translate the text"""
        # Set up HTML content with just the text preview

        
        # Update title bar
        self.title_bar.title_label.setText("Confirm Translation")
        
        # Set the HTML content
        self.label.setHtml(html_content.format(text))
        
        # Create confirm button if it doesn't exist
        if not hasattr(self, 'confirm_button'):
            print(str(ASSETS_DIR / "loading.gif"))

        self.confirm_button.show()
        
        # Hide save button during confirmation
        self.save_button.hide()
        
        # Position the window
        new_pos = QPoint(pos.x(), pos.y() - self.height())
        self.move(new_pos)
        # check if the confirm button is already connected
        try:
            self.confirm_button.click_signal.disconnect()
        except TypeError:
            pass
        self.confirm_button.click_signal.connect(partial(self.async_lookup, text, pos))

        # Show the window
        self.show()
        self.activateWindow()

    def async_lookup(self, text, pos):
        print("start async_lookup")
        """Perform an asynchronous lookup for the selected text"""
        def lookup_caption_task(text):
            ret = self.online_func(text)
            print("got ret", ret)
            return {
                'text': ret,
                'pos': pos,
            }

        def on_result(result):
            self.captionReady.emit({
                'text': result.get('text', "N/A"),
                'pos': result.get('pos', QPoint(0, 0)),
                "state": LookupState.LOADED,
                "lookup_type": LookUpType.SENTENCE,
            })

        GLOBAL_THREAD_POOL.start(Worker(lookup_caption_task, text, on_finished=on_result))


    def save_translation(self):
        self.label.page().toHtml(lambda html: print("已收藏:", html))


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
