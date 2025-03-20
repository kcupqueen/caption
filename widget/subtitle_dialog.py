from PyQt5.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QPushButton, QApplication
from PyQt5.QtCore import pyqtSignal
import sys

class SubtitleOption:
    def __init__(self, name, path, en, embed):
        self.name = name
        self.path = path
        self.en = en
        self.embed = embed

    def __str__(self):
        return f"SubtitleOption({self.name}, {self.path}, {self.en}, {self.embed})"

    def to_dialog_option(self):
        base = f"{self.name} - {self.en}"
        if self.embed:
            base += " (MKV内嵌) "
        return base

class OptionDialog(QDialog):
    option_selected = pyqtSignal(object)  # ✅ 定义一个信号，传递选择的字符串

    def __init__(self, options,w,h, fname, parent=None):
        super().__init__(parent)
        self.setWindowTitle("内置字幕选择器")
        self.selected_option = None  # 存储选择的值
        self.fname = fname
        layout = QVBoxLayout()

        # 创建单选按钮
        self.radio_buttons = []
        for option in options:
            radio = QRadioButton(option)
            layout.addWidget(radio)
            self.radio_buttons.append(radio)

        # 确认 & 取消 按钮
        self.confirm_button = QPushButton("Confirm")
        self.cancel_button = QPushButton("Cancel")
        layout.addWidget(self.confirm_button)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

        # ✅ 连接信号槽
        self.confirm_button.clicked.connect(self.emit_selected_option)
        self.cancel_button.clicked.connect(self.reject)  # 直接关闭对话框

        # size
        self.resize(w,h)

    def emit_selected_option(self):
        """Get the selected index and emit the signal"""
        for index, radio in enumerate(self.radio_buttons):
            if radio.isChecked():
                self.selected_option = index
                obj = {"index": self.selected_option,
                                           "filename": self.fname,
                                           }
                self.option_selected.emit(obj)  # ✅ Send signal
                print("emit", obj)
                self.accept()  # Close the dialog
                return
        print("No option selected!")  # Handle the case where no option is selected


# ✅ 在主窗口中监听信号
def handle_selection(selected_option):
    print(f"User selected: {selected_option}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    options = [
        "中文 - Chinese",
        "英文 - English",
        "无字幕 - No Subtitle",
        "上传外挂字幕 - Upload Subtitle",
    ]
    dialog = OptionDialog(options)

    # ✅ 连接信号到槽函数
    dialog.option_selected.connect(handle_selection)

    dialog.exec()  # 显示对话框

    # sys.exit(app.exec())  # 退出应用
    sys.exit(0)
