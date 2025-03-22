from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QStatusBar
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # 创建左侧状态栏信息
        self.left_label = QLabel("左侧信息")
        self.status_bar.addWidget(self.left_label)  # 默认靠左

        # 创建右侧状态栏信息
        self.right_label = QLabel("右侧信息")
        self.status_bar.addPermanentWidget(self.right_label)  # 右侧对齐

        # 设置窗口
        self.setGeometry(100, 100, 600, 400)
        self.setWindowTitle("QStatusBar 右侧 QLabel")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
