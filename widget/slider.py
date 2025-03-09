from PyQt5.QtWidgets import QApplication, QSlider, QVBoxLayout, QWidget, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent


class ClickableSlider(QSlider):
    def __init__(self, orientation, parent=None):  # ✅ parent 允许传 self
        super().__init__(orientation, parent)  # ✅ 传给 QSlider

    def mousePressEvent(self, event: QMouseEvent):
        if self.orientation() == Qt.Horizontal:
            click_pos = event.x()
            slider_min, slider_max = self.minimum(), self.maximum()
            slider_range = self.width()
            new_val = slider_min + (slider_max - slider_min) * click_pos / slider_range
        else:
            click_pos = event.y()
            slider_min, slider_max = self.minimum(), self.maximum()
            slider_range = self.height()
            new_val = slider_max - (slider_max - slider_min) * click_pos / slider_range

        self.setValue(int(new_val))
        self.sliderMoved.emit(int(new_val))
        self.valueChanged.emit(int(new_val))
        super().mousePressEvent(event)  # 调用父类方法，保持默认行为


class VideoSlider(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)  # ✅ 只传 parent，不要传 orientation

        layout = QVBoxLayout(self)
        self.slider = ClickableSlider(Qt.Horizontal, self)  # ✅ 传 self 作为 parent
        self.slider.setMinimum(0)
        self.slider.setMaximum(100)
        self.label = QLabel("Value: 0")

        layout.addWidget(self.slider)
        layout.addWidget(self.label)

        self.slider.valueChanged.connect(self.on_value_changed)

    def on_value_changed(self, value):
        self.label.setText(f"Value: {value}")


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = VideoSlider()
    window.setMinimumSize(400, 100)
    window.show()
    sys.exit(app.exec_())

