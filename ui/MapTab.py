from random import random

import matplotlib
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtMultimedia import QSoundEffect



class PlotDataThread(QThread):
    data_ready = pyqtSignal(np.ndarray, np.ndarray)  # Сигнал для передачи данных графика

    def run(self):
        # Генерация случайных данных (имитация долгих вычислений)
        while True:
            x = np.linspace(0, 10, 100)  # 100 точек на оси X
            y = np.random.rand(100) * 10  # Случайные данные для оси Y от 0 до 10
            self.data_ready.emit(x, y)  # Отправляем данные в основной поток
            self.msleep(50)  # Эмуляция задержки в 1 секунду

class MapTab(QWidget):
    def __init__(self, logger):
        super().__init__()
        layout = QVBoxLayout()
        logger.log("This is a log", "warning", "mapTab")
        self.canvas = FigureCanvas(plt.figure())
        layout.addWidget(self.canvas)
        self.plot_thread = PlotDataThread()
        self.plot_thread.data_ready.connect(self.update_plot)
        self.plot_thread.start()
        self.setLayout(layout)

    def update_plot(self, x, y):
        # Очищаем текущий график, чтобы предотвратить наложение осей
        self.canvas.figure.clf()  # Полностью очищаем текущую фигуру

        # Создаем новый subplot
        ax = self.canvas.figure.add_subplot(111)
        ax.plot(x, y)
        ax.set_title("Случайный график")
        ax.set_xlabel("Ось X")
        ax.set_ylabel("Ось Y")

        # Перерисовываем график
        self.canvas.draw()

        self.sound = QSoundEffect(self)
        self.sound.setSource(QUrl.fromLocalFile(r"C:\Users\verrg\Projects\SNV\assets\finished.wav"))

        self.sound.play()
