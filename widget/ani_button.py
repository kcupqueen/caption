from PyQt5.QtWidgets import QApplication, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtGui import QMovie
from PyQt5.QtCore import Qt
import os

class GifButton(QPushButton):
    click_signal = pyqtSignal()  # ✅ 定义一个信号

    def __init__(self, text, gif_path):
        super().__init__(text)
        self.setFixedSize(160, 40)

        # 创建 QLabel 播放 GIF
        self.gif_label = QLabel(self)
        self.gif_label.setFixedSize(20, 20)  # 控制 GIF 大小
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # GIF 居左

        # 加载 GIF
        self.movie = QMovie(gif_path)  # 你的 GIF 文件
        self.movie.setScaledSize(self.gif_label.size())  # 控制 GIF 大小
        self.gif_label.setMovie(self.movie)

        # 默认显示 GIF 的第一帧（静止状态）
        self.movie.jumpToFrame(0)

        # 设置布局管理器
        layout = QHBoxLayout(self)
        layout.addWidget(self.gif_label)
        layout.addStretch()  # 添加弹性空间
        layout.setContentsMargins(5, 0, 5, 0)  # 设置边距
        self.setText(text)  # 直接设置按钮文本，不需要新建QPushButton

        # 绑定点击事件
        self.clicked.connect(self.start_animation)

    def start_animation(self):
        """点击按钮后播放 GIF 并在 1 秒后停止"""
        print("start_animation")
        self.click_signal.emit()
        self.movie.start()  # 播放 GIF
        QTimer.singleShot(5000, self.stop_animation)  # 1 秒后停止

    def stop_animation(self):
        """停止 GIF 并回到第一帧"""
        self.movie.stop()
        self.movie.jumpToFrame(0)  # 返回第一帧，保持静止状态

if __name__ == "__main__":
    app = QApplication([])
    current_dir = os.path.dirname(os.path.abspath(__file__))
    gif_path = os.path.join(current_dir, "../assets", "loading.gif")
    print(f"Loading GIF from: {gif_path}")  # 打印实际路径以验证
    button = GifButton("点击加载", gif_path)
    button.show()
    app.exec()
