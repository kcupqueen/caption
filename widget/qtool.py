import sys
from PyQt5.QtWidgets import QApplication, QTextEdit, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtGui import QTextCursor, QIcon
from PyQt5.QtCore import Qt, QPoint, QEvent, pyqtSignal

from caption.translate import OnlineTranslator, SentenceTranslation


class FloatingTranslation(QWidget):
    """悬浮翻译窗口（点击外部自动关闭）"""
    windowClosed = pyqtSignal(dict)  # Modified to accept a dictionary parameter
    captionReady = pyqtSignal(dict)  # Added a signal to emit a string
    
    def __init__(self, parent=None, confirm=False, onlineTranslator=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: white; border: 1px solid black; padding: 5px;")

        self.setAttribute(Qt.WA_DeleteOnClose)  # 关闭后释放内存 ✅

        # 翻译文本
        self.label = QLabel("翻译内容", self)
        self.save_button = QPushButton("⭐ 收藏")
        self.save_button.clicked.connect(self.save_translation)
        self.confirm = confirm
        self.onlineTranslator = onlineTranslator
        if self.confirm:
            self.confirm_button = QPushButton(QIcon("assets/ai_search.png"), "AI explain")
            self.confirm_button.clicked.connect(self.confirm_translation)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        if self.confirm:
            layout.addWidget(self.confirm_button)
        layout.addWidget(self.save_button)


        self.setLayout(layout)

        # 监听全局鼠标点击事件
        QApplication.instance().installEventFilter(self)


    def confirm_translation(self):
        print("clicked confirm button")
        if isinstance(self.onlineTranslator, OnlineTranslator):
            ret = self.onlineTranslator.lookup(self.label.text())
            if ret and isinstance(ret, SentenceTranslation):
                render = ret.to_html()
                # to be continued


    def set_translation(self, text, pos, state, confirm=False):
        """设置翻译内容，并移动到指定位置"""
        if state == "loaded":
            self.label.setText(text)  # 模拟翻译
        else:
            self.label.setText(text)  # 模拟翻译
        self.move(pos)
        self.show()
        if confirm:
            # hide collect button
            self.save_button.hide()

    def save_translation(self):
        """收藏翻译"""
        print("已收藏:", self.label.text())

    def eventFilter(self, obj, event):
        """监听鼠标点击事件，判断是否点击到了窗口外部"""
        if event.type() == QEvent.MouseButtonPress:
            if self.isHidden():
                print("[FloatingTranslation] ignore not showing...")
                return super().eventFilter(obj, event)

            clicked_widget = QApplication.widgetAt(event.globalPos())
            
            # 直接比较是否是 playbutton
            if clicked_widget == self.parent().playbutton:  # 最具体的方式
                self.hide()
                print('playbutton clicked')
                return super().eventFilter(obj, event)
            
            if not self.geometry().contains(event.globalPos()):  # 判断是否点击到窗口外部
                print("[FloatingTranslation] clicked outside, closing...", self.isHidden())
                self.hide()
                self.windowClosed.emit({
                    'test': 'test'
                })  # emit a dictionary signal
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
