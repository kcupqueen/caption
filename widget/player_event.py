from PyQt5.QtGui import QMouseEvent
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget


def mouse_press_event(w: QWidget, event: QMouseEvent):
    widget = w.childAt(event.pos())  # 检测点击的控件
    print(f"点击位置: {event.pos()}")

    if widget:
        print(f"点击了控件: {widget.objectName()}")
    else:
        print("点击在空白区域")

    if event.button() == Qt.LeftButton:
        print("鼠标左键点击")
    elif event.button() == Qt.RightButton:
        print("鼠标右键点击")
