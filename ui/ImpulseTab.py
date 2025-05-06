import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QLineEdit, \
    QPushButton, QFileDialog, QHeaderView, QSizePolicy
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_template import FigureCanvas
from matplotlib.figure import Figure

from ui.CorrelationTab import MplCanvas


class PulseCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=10, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.axes = self.fig.add_subplot(111)

    def plot_pulses(self, data):
        """Отрисовка импульсов по данным с соединением разрывов"""
        if not data or len(data) != 5:
            return

        num_channels, channels, counts, starts, stops = data

        # Очищаем предыдущий график
        self.fig.clear()

        # Если нет данных - выходим
        if num_channels == 0:
            self.draw()
            return

        # Создаем subplot для каждого канала
        self.axes = self.fig.subplots(num_channels, 1, sharex=True)

        # Если только один канал, преобразуем в массив для единообразия
        if num_channels == 1:
            self.axes = [self.axes]

        # Определяем общие пределы по времени
        all_times = starts + stops
        max_time = max(all_times) if all_times else 100
        time_margin = max_time * 0.1  # 10% отмашка

        current_idx = 0
        for i, channel in enumerate(channels):
            ax = self.axes[i]
            ax.clear()

            # Настройки графика
            ax.set_title(f'Канал {channel}')
            ax.set_ylim(-0.01, 1.2)
            ax.set_yticks([])
            ax.grid(True, linestyle='--', alpha=0.5)

            # Собираем все точки для соединения
            all_points = []
            for j in range(counts[i]):
                start = starts[current_idx + j]
                stop = stops[current_idx + j]
                all_points.extend([(start, 0), (start, 1), (stop, 1), (stop, 0)])

            # Сортируем точки по времени
            all_points.sort(key=lambda x: x[0])

            # Рисуем соединенные линии
            if all_points:
                x_vals, y_vals = zip(*all_points)
                ax.plot(x_vals, y_vals, 'b-', linewidth=2)

                # Подписываем импульсы
                for j in range(counts[i]):
                    start = starts[current_idx + j]
                    stop = stops[current_idx + j]
                    ax.text((start + stop)/2, 1.1, f'{j+1}',
                           ha='center', va='center', fontsize=8)

            current_idx += counts[i]

            # Настройки для последнего subplot
            if i == num_channels - 1:
                ax.set_xlim(-time_margin, max_time + time_margin)
                ax.set_xlabel('Время')

        self.fig.tight_layout()
        self.draw()

class ImpulseTab(QWidget):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger

        self.canvas = PulseCanvas(self, width=10, height=10, dpi=100)
        self.data = None
        self.save_path = None
        self.open_path = None
        self.simulation_time = 500
        layout = QHBoxLayout()
        layout.addWidget(self.canvas)
        input_layout = QVBoxLayout()
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['канал', 'старт', 'стоп'])
        input_layout.addWidget(self.table)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        add_impulse_layout = QHBoxLayout()
        self.channel_id = QLineEdit()
        self.channel_id.setPlaceholderText("Канал")
        self.impulse_start = QLineEdit()
        self.impulse_start.setPlaceholderText("Старт")
        self.impulse_stop = QLineEdit()
        self.impulse_stop.setPlaceholderText("Стоп")
        add_button = QPushButton("Добавить")
        add_button.clicked.connect(self.add_impulse)
        add_impulse_layout.addWidget(self.channel_id)
        add_impulse_layout.addWidget(self.impulse_start)
        add_impulse_layout.addWidget(self.impulse_stop)
        add_impulse_layout.addWidget(add_button)

        input_layout.addLayout(add_impulse_layout)

        parameters_layout = QVBoxLayout()
        self.repeat_time_field = QLineEdit()
        self.repeat_time_field.setPlaceholderText("Время повтора")

        self.pulse_scale_field = QLineEdit()
        self.pulse_scale_field.setPlaceholderText("pulse_scale_field")

        self.rep_scale_field = QLineEdit()
        self.rep_scale_field.setPlaceholderText("rep_scale_field")

        parameters_layout.addWidget(self.repeat_time_field)
        parameters_layout.addWidget(self.pulse_scale_field)
        parameters_layout.addWidget(self.rep_scale_field)

        input_layout.addLayout(parameters_layout)


        delete_button = QPushButton("Удалить строку")
        delete_button.clicked.connect(self.delete_selected_row)
        load_conf_button = QPushButton("Загрузить в конструктор")
        load_conf_button.clicked.connect(self.load_pulse_data)
        save_conf_button = QPushButton("Сохранить в файл")
        save_conf_button.clicked.connect(self.save_pulse_data)
        input_layout.addWidget(delete_button)
        input_layout.addWidget(load_conf_button)
        input_layout.addWidget(save_conf_button)

        layout.addLayout(input_layout)

        self.setLayout(layout)

    def get_data_from_table(self):
        # Словарь для группировки данных по каналам
        channels_data = {}

        # Собираем данные из таблицы
        for row in range(self.table.rowCount()):
            channel_item = self.table.item(row, 0)  # Колонка "Канал"
            start_item = self.table.item(row, 1)  # Колонка "Старт"
            stop_item = self.table.item(row, 2)  # Колонка "Стоп"

            if channel_item and start_item and stop_item:
                try:
                    channel = int(channel_item.text())
                    start = int(start_item.text())
                    stop = int(stop_item.text())

                    # Добавляем данные в словарь по каналам
                    if channel not in channels_data:
                        channels_data[channel] = {
                            'impulse_count': 0,
                            'starts': [],
                            'stops': []
                        }

                    channels_data[channel]['impulse_count'] += 1
                    channels_data[channel]['starts'].append(start)
                    channels_data[channel]['stops'].append(stop)

                except ValueError:
                    self.logger.error(f"Ошибка преобразования данных в строке {row + 1}")
                    continue

        # Формируем выходные массивы
        channel_numbers = []
        impulse_counts = []
        start_times = []
        stop_times = []

        # Сортируем каналы по порядку их первого появления
        sorted_channels = sorted(channels_data.keys(),
                                 key=lambda ch: next(i for i, row in enumerate(range(self.table.rowCount()))
                                                     if int(self.table.item(row, 0).text()) == ch))

        for channel in sorted_channels:
            data = channels_data[channel]
            channel_numbers.append(channel)
            impulse_counts.append(data['impulse_count'])
            start_times.extend(data['starts'])
            stop_times.extend(data['stops'])

        # Сохраняем данные в требуемом формате
        self.data = (
            len(channel_numbers),  # количество уникальных каналов
            channel_numbers,  # массив номеров каналов (в порядке первого появления)
            impulse_counts,  # массив количества импульсов для каждого канала
            start_times,  # все времена стартов (сгруппированные по каналам)
            stop_times  # все времена стопов (сгруппированные по каналам)
        )

        return self.data

    @staticmethod
    def add_centered_item(table, row, col, text):
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table.setItem(row, col, item)
        return item

    def add_impulse(self):
        row = self.table.rowCount()
        self.table.insertRow(row)

        # Создаем элементы с выравниванием по центру
        item_channel = QTableWidgetItem(self.channel_id.text())
        item_channel.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        item_start = QTableWidgetItem(self.impulse_start.text())
        item_start.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        item_stop = QTableWidgetItem(self.impulse_stop.text())
        item_stop.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        # Устанавливаем элементы в таблицу
        self.table.setItem(row, 0, item_channel)
        self.table.setItem(row, 1, item_start)  # Обратите внимание: исправлен индекс с 2 на 1
        self.table.setItem(row, 2, item_stop)  # и с 3 на 2 (т.к. индексация с 0)

        self.data = self.get_data_from_table()
        self.update_plots()

    def delete_selected_row(self):
        """Удаляет выбранную строку из таблицы и обновляет данные"""
        try:

            # Проверяем, есть ли данные в таблице
            if self.table.rowCount() == 0:
                self.logger.log("Таблица пуста - нечего удалять", "Warning", "delete_selected_row")
                return

            selected_row = self.table.currentRow()

            # Проверяем, что строка выбрана
            if selected_row < 0:
                self.logger.log("Пожалуйста, выберите строку для удаления", "Info", "delete_selected_row")
                return

            # УДАЛЕНИЕ СТРОКИ (основная операция)
            self.table.removeRow(selected_row)

            # Обновляем данные после удаления
            self.data = self.get_data_from_table()
            self.update_plots()

        except Exception as e:
            error_msg = f"Ошибка при удалении строки: {str(e)}"
            self.logger.log(error_msg, "Error", "delete_selected_row")

    def save_pulse_data(self):
        """Сохраняет данные импульсов в файл в формате:
        (num_channels, channels, counts, starts, stops)"""
        try:
            if not hasattr(self, 'data') or len(self.data) != 5:
                self.logger.log("Нет данных для сохранения", "Error", "save_pulse_data")
                return False
        except Exception as e:
            self.logger.log(e, "Error", "save_pulse_data")

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить конфигурацию импульсов",
            "",
            "Pulse Config Files (*.pcfg);;All Files (*)"
        )
        if not filename:
            return False

        try:
            num_channels, channels, counts, starts, stops = self.data

            # Формируем строку для сохранения
            data_str = (
                f"({num_channels}, {channels}, {counts}, {starts}, {stops}, {self.repeat_time_field.text()}, {self.pulse_scale_field.text()}, {self.rep_scale_field.text()})"
            )

            # Записываем в файл
            with open(filename, 'w') as f:
                f.write(data_str)

            self.logger.log(f"Данные успешно сохранены в {filename}", "Info", "save_pulse_data")

            return True

        except Exception as e:
            self.logger.log(f"Ошибка при сохранении: {str(e)}", "Error", "save_pulse_data")
            return False

    def load_pulse_data(self):
        """Загружает данные импульсов и параметры из файла"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить конфигурацию импульсов",
            "",
            "Pulse Config Files (*.pcfg);;All Files (*)"
        )
        if not filename:
            return False

        try:
            with open(filename, 'r') as f:
                content = f.read().strip()

            # Удаляем внешние скобки если они есть
            if content.startswith('(') and content.endswith(')'):
                content = content[1:-1].strip()

            # Разбиваем строку на элементы
            elements = []
            current = ""
            in_list = False
            for char in content:
                if char == '[':
                    in_list = True
                    current += char
                elif char == ']':
                    in_list = False
                    current += char
                elif char == ',' and not in_list:
                    elements.append(current.strip())
                    current = ""
                else:
                    current += char
            elements.append(current.strip())

            # Проверяем минимальное количество элементов
            if len(elements) < 5:
                raise ValueError("Недостаточно параметров в файле (требуется минимум 5)")

            # Функция для безопасного парсинга списков
            def parse_list(s):
                s = s.strip()
                if not (s.startswith('[') and s.endswith(']')):
                    raise ValueError(f"Ожидается список в квадратных скобках: {s}")
                return [int(item.strip()) for item in s[1:-1].split(',') if item.strip()]

            # Основные параметры
            num_channels = int(elements[0])
            channels = parse_list(elements[1])
            counts = parse_list(elements[2])
            starts = parse_list(elements[3])
            stops = parse_list(elements[4])

            # Дополнительные параметры (устанавливаем в поля интерфейса)
            if len(elements) > 5:
                self.repeat_time_field.setText(elements[5].strip())
            if len(elements) > 6:
                self.pulse_scale_field.setText(elements[6].strip())
            if len(elements) > 7:
                self.rep_scale_field.setText(elements[7].strip())

            # Проверяем согласованность данных
            if len(channels) != len(counts):
                raise ValueError("Количество каналов не совпадает с количеством счетчиков")

            total_pulses = sum(counts)
            if len(starts) != total_pulses or len(stops) != total_pulses:
                raise ValueError("Количество стартов/стопов не соответствует количеству импульсов")

            # Заполняем таблицу с выравниванием по центру
            self.table.setRowCount(0)
            current_idx = 0
            for ch, cnt in zip(channels, counts):
                for i in range(cnt):
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.add_centered_item(self.table, row, 0, str(ch))
                    self.add_centered_item(self.table, row, 1, str(starts[current_idx + i]))
                    self.add_centered_item(self.table, row, 2, str(stops[current_idx + i]))
                current_idx += cnt

            self.data = self.get_data_from_table()
            self.update_plots()

            self.logger.log(f"Конфигурация импульсов загружена из {filename}", "Info", "load_pulse_data")
            return True

        except Exception as e:
            error_msg = f"Ошибка при загрузке: {str(e)}"
            self.logger.log(error_msg, "Error", "load_pulse_data")
            return False

    def update_plots(self):
        print(self.data)
        """Обновление графиков импульсов"""
        self.canvas.plot_pulses(self.data)


