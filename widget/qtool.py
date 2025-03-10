import sys
from PyQt5.QtWidgets import QApplication, QTextEdit, QLabel, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import Qt, QPoint

class FloatingTranslation(QWidget):
    """悬浮翻译窗口（可独立使用）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)  # 悬浮窗口
        self.setStyleSheet("background-color: white; border: 1px solid black; padding: 5px;")

        # 翻译文本
        self.label = QLabel("翻译内容", self)

        # 收藏按钮
        self.save_button = QPushButton("⭐ 收藏")
        self.save_button.clicked.connect(self.save_translation)

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

        self.saved_translations = []  # 存储收藏的翻译
        self.relative_pos = QPoint(0, 0)  # 记录相对位置
        self.main_window = parent  # 绑定主窗口

        if self.main_window:
            self.main_window.installEventFilter(self)  # 监听主窗口事件

    def set_translation(self, text, pos):
        """更新翻译文本，并显示在指定位置"""
        self.label.setText(f"翻译: {text[::-1]}")  # 模拟翻译（反转文本）
        self.relative_pos = pos - self.main_window.pos() if self.main_window else QPoint(0, 0)
        self.move(pos)
        self.show()

    def save_translation(self):
        """收藏翻译"""
        translation_text = self.label.text()
        if translation_text not in self.saved_translations:
            self.saved_translations.append(translation_text)
            print("已收藏:", translation_text)  # 这里可以改成存入数据库或文件

    def eventFilter(self, obj, event):
        """监听主窗口的移动事件"""
        if obj == self.main_window and event.type() == event.Move:
            self.move(self.main_window.pos() + self.relative_pos)
        return super().eventFilter(obj, event)

    def focusOutEvent(self, event):
        """当失去焦点（点击外部）时自动关闭"""
        print('focusOutEvent')
        self.close()

class TranslatorApp(QWidget):
    """主界面"""
    def __init__(self):
        super().__init__()

        self.textEdit = QTextEdit()
        self.textEdit.setText("Select any text to translate.")
        self.textEdit.mouseReleaseEvent = self.show_translation  # 监听鼠标释放事件

        self.floatingWindow = FloatingTranslation(self)  # 创建可复用的悬浮翻译窗口

        layout = QVBoxLayout()
        layout.addWidget(self.textEdit)
        self.setLayout(layout)

    def show_translation(self, event):
        """选中文字后显示悬浮翻译窗口"""
        cursor = self.textEdit.textCursor()
        if cursor.hasSelection():
            selected_text = cursor.selectedText()
            cursor_rect = self.textEdit.cursorRect(cursor)
            pos = self.textEdit.mapToGlobal(cursor_rect.bottomRight())  # 获取全局坐标
            self.floatingWindow.set_translation(selected_text, pos)  # 传递位置数据

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslatorApp()
    window.resize(500, 300)
    window.show()
    sys.exit(app.exec_())
