from PyQt5.QtCore import QThreadPool, QRunnable, pyqtSignal, QObject, QCoreApplication
import time

GLOBAL_THREAD_POOL = QThreadPool.globalInstance()



class WorkerSignals(QObject):
    """用于发射任务完成信号"""
    finished = pyqtSignal(object)  # 传递任务结果或标识

class Worker(QRunnable):
    """支持回调的 Worker"""
    def __init__(self, func, *args, on_finished=None, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.on_finished = on_finished  # 任务完成后的回调
        self.signals = WorkerSignals()  # 信号对象

        if self.on_finished:
            self.signals.finished.connect(self.on_finished)

    def run(self):
        """执行任务"""
        result = self.func(*self.args, **self.kwargs)  # 运行主任务
        self.signals.finished.emit(result)  # 任务完成后发射信号

def example_task(name, duration):
    """示例任务"""
    print(f"任务 {name} 开始")
    time.sleep(duration)  # 模拟耗时操作
    print(f"任务 {name} 完成")
    return f"任务 {name} 结果"

def on_result(result):
    """任务完成后调用的回调函数"""
    print(f"任务完成，结果: {result}")

if __name__ == "__main__":
    app = QCoreApplication([])  # 创建 Qt 应用
    thread_pool = QThreadPool.globalInstance()  # 获取全局线程池

    # 创建并提交任务
    thread_pool.start(Worker(example_task, "A", 2, on_finished=on_result))
    thread_pool.start(Worker(example_task, "B", 3, on_finished=on_result))
    thread_pool.start(Worker(example_task, "C", 1, on_finished=on_result))

    app.exec()  # 运行 Qt 事件循环
