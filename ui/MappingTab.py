import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLineEdit, QPushButton, QHBoxLayout, QSizePolicy, QLabel
from matplotlib.backends.backend_qt import NavigationToolbar2QT

from ui.CorrelationTab import MplCanvas


class MappingTab(QWidget):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger

        # Основной вертикальный layout
        main_layout = QVBoxLayout(self)

        # Виджеты для графика
        self.canvas = MplCanvas(self, width=5, height=4, dpi=90)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # Добавляем toolbar без stretch factor
        main_layout.addWidget(self.toolbar)

        # Горизонтальный layout для графика и элементов управления
        content_layout = QHBoxLayout()

        # Layout с элементами управления
        control_layout = QVBoxLayout()

        # Создаем и добавляем элементы управления
        self.x_coord_range_field = QLineEdit()
        self.x_coord_range_field.setPlaceholderText("Диапазон x")
        self.y_coord_range_field = QLineEdit()
        self.y_coord_range_field.setPlaceholderText("Диапазон y")
        self.step_field = QLineEdit()
        self.step_field.setPlaceholderText("Шаг")
        self.collect_time_field = QLineEdit()
        self.collect_time_field.setPlaceholderText("Время накопления")
        self.save_button = QPushButton("Сохранить")
        self.load_button = QPushButton("Загрузить")
        self.action_button = QPushButton("Начать")

        control_layout.addWidget(self.x_coord_range_field)
        control_layout.addWidget(self.y_coord_range_field)
        control_layout.addWidget(self.step_field)
        control_layout.addWidget(self.collect_time_field)
        control_layout.addWidget(self.save_button)
        control_layout.addWidget(self.load_button)
        control_layout.addWidget(self.action_button)

        # Добавляем график и элементы управления в горизонтальный layout
        content_layout.addWidget(self.canvas, stretch=7)
        content_layout.addLayout(control_layout, stretch=1)

        # Добавляем основной контент с растягиванием
        main_layout.addLayout(content_layout)

        # Настройка политик размеров
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )

        # Пример данных
        data = np.random.random((12, 12))
        self.canvas.axes.imshow(data)