from PyQt5.QtCore import QThread, pyqtSignal

class QtThread(QThread):
    finished = pyqtSignal(object)  # 任务完成后发出信号，支持任意类型的结果

    def __init__(self, func, *args, **kwargs):
        """
        :param func: 需要执行的函数
        :param args: 传递给函数的参数
        :param kwargs: 传递给函数的关键字参数
        """
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        """运行任务"""
        try:
            result = self.func(*self.args, **self.kwargs)  # 执行传入的函数
            self.finished.emit(result)  # 任务完成后发送信号
        except Exception as e:
            self.finished.emit(f"Error: {e}")  # 发生异常时发送错误信息

"""
def lookup_caption_task(text):
    return lookup_caption(text, LookUpType.WORD if ' ' not in text else LookUpType.SENTENCE)

def on_result(result):
    print("翻译结果:", result)

# 创建线程并启动
thread = QtThread(lookup_caption_task, "hello")
thread.finished.connect(on_result)  # 连接信号
thread.start()

"""