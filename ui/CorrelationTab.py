import struct
import time
from collections import deque

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog
from fast_histogram import histogram1d
from matplotlib.backends.backend_qt import NavigationToolbar2QT
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import pcapy

class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class CounterWorker(QThread):
    def __init__(self, *args):
        super(CounterWorker, self).__init__()
        self.args = args
        self.interval = 0.1
        self.window_size = 100
        self.canvas = self.args[0]
        self.photon_data = self.args[1]
        self.x_data = np.linspace(0, self.window_size, self.window_size)
        self.y_data_0 = np.zeros(self.window_size)
        self.y_data_1 = np.zeros(self.window_size)
        self.line_0, = self.canvas.axes.plot(self.x_data, self.y_data_0, lw=2, color="red", label="Канал 0")
        self.line_1, = self.canvas.axes.plot(self.x_data, self.y_data_1, lw=2, color="blue", label="Канал 1")
        self.canvas.axes.set_xticks([])
        self.canvas.axes.set_title("Счёт фотонов")
        self.canvas.axes.set_xlabel('Время')
        self.canvas.axes.set_ylabel('Отсчеты')
        self.canvas.axes.legend(loc="upper right")
        self.canvas.axes.grid()
        self.is_killed = False

    def run(self):
        while not self.is_killed:
            try:
                data_point_0 = self.photon_data[-1]['cnt_photon_1']
                data_point_1 = self.photon_data[-1]['cnt_photon_2']
            except Exception:
                data_point_0 = 0
                data_point_1 = 0

            self.y_data_0 = np.roll(self.y_data_0, -1)
            self.y_data_1 = np.roll(self.y_data_1, -1)

            self.y_data_0[-1] = data_point_0
            self.y_data_1[-1] = data_point_1

            max_data = max(np.max(self.y_data_0),np.max(self.y_data_1))
            min_data = min(np.min(self.y_data_0),np.min(self.y_data_1))

            self.canvas.axes.set_xlim(0, 100)
            self.canvas.axes.set_ylim(min_data, max_data + 5)

            self.line_0.set_ydata(self.y_data_0)
            self.line_1.set_ydata(self.y_data_1)

            self.canvas.draw()
            self.canvas.flush_events()

            # FIXME Обновление каждые 100 мс, можно вынести потом в отдельную переменную
            time.sleep(0.1)

        self.canvas.axes.clear()
        self.canvas.axes.cla()

class HistWorker(QThread):
    result_ready = pyqtSignal(np.ndarray)

    def __init__(self, logger, data, bins, tau_max_ns):
        super().__init__()
        self.logger = logger
        self.data = data
        self.bins = bins
        self.tau_max_ns = tau_max_ns

    def run(self):
        deltas = np.concatenate([np.subtract.outer(t1, t2).ravel() for t1, t2 in self.data])
        valid = deltas[(deltas > -self.tau_max_ns) & (deltas < self.tau_max_ns)]
        hist = histogram1d(valid, bins=len(self.bins) - 1, range=(-self.tau_max_ns, self.tau_max_ns))

        self.result_ready.emit(hist)


class SniffThread(QThread):
    packet_signal = pyqtSignal(dict)

    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.running = True
        self.cap = None

    def run(self):
        #self.logger.log("I am photon counter", "Info", "SniffThread")

        try:

            self.cap = pcapy.open_live("Ethernet", 106, 0, 0)
            self.cap.setfilter("udp and src host 192.168.1.2")

            self.logger.log("Sniffer started on 'Ethernet'", "Info", "SniffThread")

            # Основной цикл захвата пакетов
            self.cap.loop(0, self.packet_callback)

        except Exception as e:
            self.logger.log(f"Sniffer error: {e}", "Error", "SniffThread")

    def packet_callback(self, header, packet):
        """Обработка каждого пакета"""
        #print("Got packet")
        if not self.running:
            return

        try:
            # Пропускаем Ethernet/IP/UDP заголовки
            payload = packet[42:]

            # Проверка размера
            if len(payload) < 64:
                self.logger.log("Некорректный размер пакета", "Error", "packet_callback")
                return

            # Распаковка служебных байт
            package_id = struct.unpack('<H', payload[1:3])[0]
            byte6 = struct.unpack('<B', payload[5:6])[0]

            flag = (byte6 >> 7) & 1
            flag_valid = byte6 & 0x1
            flag_pos = (byte6 & 0x10) >> 4
            flag_neg = (byte6 & 0x8) >> 3

            # Счётчики фотонов
            cnt_photon_1 = struct.unpack('<H', payload[6:8])[0]
            cnt_photon_2 = struct.unpack('<H', payload[8:10])[0]

            # Временные метки TP1
            tp1 = [int.from_bytes(payload[10 + 4 * i:14 + 4 * i], byteorder="little") for i in range(6)]
            tp1_a = [np.round((t & 0x1F) * 0.18, 1) for t in tp1]  # ns
            tp1_b = [np.round((t >> 7) * 5, 1) for t in tp1]        # ns
            tp1_r = [a + b for a, b in zip(tp1_a, tp1_b)]

            # Временные метки TP2
            tp2 = [int.from_bytes(payload[34 + 4 * i:38 + 4 * i], byteorder="little") for i in range(6)]
            tp2_a = [np.round((t & 0x1F) * 0.18, 1) for t in tp2]  # ns
            tp2_b = [np.round((t >> 7) * 5, 1) for t in tp2]        # ns
            tp2_r = [a + b for a, b in zip(tp2_a, tp2_b)]

            # Формируем результат
            result = {
                "package_id": package_id,
                "flag": flag,
                "flag_valid": flag_valid,
                "flag_neg": flag_neg,
                "flag_pos": flag_pos,
                "cnt_photon_1": cnt_photon_1,
                "cnt_photon_2": cnt_photon_2,
                "tp1_r": np.array(list(set(tp1_r))),
                "tp2_r": np.array(list(set(tp2_r))),
            }

            # Передаём результат, если пакет валиден
            if flag_valid == 1:
                print("signal emitted")
                self.packet_signal.emit(result)

        except Exception as e:
            self.logger.log(f"Неудачный парсинг пакета: {e}", "Error", "packet_callback")

    def stop(self):
        """Останавливает цикл cap.loop()"""
        self.running = False
        try:
            if self.cap:
                self.cap.breakloop()  # прерывает cap.loop()
                self.logger.log("Sniffer stopped", "Info", "SniffThread")
        except Exception as e:
            self.logger.log(f"Error stopping sniffer: {e}", "Error", "SniffThread")
        self.quit()


class CorrelationTab(QWidget):
    def __init__(self, logger):
        super().__init__()
        self.plot_thread = None
        self.logger = logger
        self.photon_data = deque(maxlen=10000)
        self.hist_data = None
        self.bins = None
        self.tau_max_ns = 100
        self.bin_width_ns = 0.1
        self.num_bins = None
        self.init = False

        layout = QVBoxLayout()

        main_layout = QHBoxLayout()

        self.canvas = MplCanvas(self, width=5, height=4, dpi=90)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setTitle("g2", size="13pt")
        self.plot_widget.setLabel("left", "Счёты", size="13pt")
        self.plot_widget.setLabel("bottom", "Время [нс]", size="13pt")
        self.plot_widget.showGrid(x=True, y=True)

        counter_layout = QVBoxLayout()
        toolbar = NavigationToolbar2QT(self.canvas, self)
        counter_layout.addWidget(toolbar)
        counter_layout.addWidget(self.canvas)

        main_layout.addLayout(counter_layout, stretch=1)
        main_layout.addWidget(self.plot_widget, stretch=1)

        control_layout = QHBoxLayout()
        self.control_button = QPushButton("Старт")
        self.control_button.clicked.connect(self.control_button_clicked)

        self.save_button = QPushButton("Сохранить гистограмму")
        self.save_button.clicked.connect(self.save_histogram)
        self.load_button = QPushButton("Загрузить гистограмму")
        self.load_button.clicked.connect(self.load_histogram)

        control_layout.addWidget(self.control_button)
        control_layout.addWidget(self.save_button)
        control_layout.addWidget(self.load_button)

        layout.addLayout(main_layout)
        layout.addLayout(control_layout)

        self.setLayout(layout)

        self.sniff_thread = SniffThread(self.logger)
        self.sniff_thread.packet_signal.connect(self.packet_received)

    def packet_received(self, packet):
        if not self.init and packet['flag']:
            # Инициализация при первом флаговом пакете
            self.plot_thread = CounterWorker(self.canvas, self.photon_data)
            self.plot_thread.start()
            
            self.num_bins = int(np.round(self.tau_max_ns / self.bin_width_ns))
            self.bins = np.linspace(-self.tau_max_ns, self.tau_max_ns, self.num_bins + 1)
            self.hist_data = np.zeros(self.num_bins)
            self.init = True
            self.logger.log("Инициализация гистограммы", "Info", "CorrelationTab")

        if self.init:
            self.photon_data.append(packet)
            if packet['flag']:
                self.process_data()

    def process_data(self):
        all_t1 = [d["tp1_r"] for d in self.photon_data]
        all_t2 = [d["tp2_r"] for d in self.photon_data]

        # Запуск расчета гистограммы
        self.hist_worker = HistWorker(
            self.logger,
            list(zip(all_t1, all_t2)),
            self.bins,
            self.tau_max_ns
        )
        self.hist_worker.result_ready.connect(self.update_plot)
        self.hist_worker.start()

    def update_plot(self, new_hist):
        try:
            if self.hist_data is None:
                return

            # Накопление данных
            self.hist_data += new_hist

            # Обновление графика
            self.plot_widget.clear()
            self.plot_widget.plot(
                self.bins,
                self.hist_data,
                stepMode=True,
                fillLevel=0)

        except Exception as e:
            self.logger.log(f"Ошибка обновления графика: {str(e)}", "Error", "update_plot")

    def control_button_clicked(self):
        if not self.sniff_thread.isRunning():
            self.photon_data = deque(maxlen=10000)
            self.hist_data = None

            self.plot_widget.clear()
            self.sniff_thread.start()
            self.control_button.setText("Стоп")
        else:
            self.sniff_thread.requestInterruption()
            self.sniff_thread.terminate()
            self.plot_thread.is_killed = True
            self.init = False

            self.control_button.setText("Старт")

    def save_histogram(self):
        """Сохраняет гистограмму в файл"""
        if self.hist_data is None or len(self.hist_data) == 0:
            self.logger.log("Нет данных гистограммы для сохранения", "Warning", "save_histogram")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить гистограмму",
            "",
            "CSV Files (*.csv);;NPZ Files (*.npz);;All Files (*)"
        )

        if not filename:
            return

        try:
            if filename.endswith('.csv'):
                # Сохранение в CSV
                import csv
                with open(filename, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Time (ns)', 'Counts'])
                    for time, count in zip(self.bins[:-1], self.hist_data):
                        writer.writerow([time, count])
            elif filename.endswith('.npz'):
                # Сохранение в бинарном формате NumPy
                np.savez(
                    filename,
                    bins=self.bins,
                    hist_data=self.hist_data,
                    tau_max_ns=self.tau_max_ns,
                    bin_width_ns=self.bin_width_ns
                )
            else:
                # Сохранение в текстовом формате
                with open(filename, 'w') as f:
                    f.write(f"tau_max_ns: {self.tau_max_ns}\n")
                    f.write(f"bin_width_ns: {self.bin_width_ns}\n")
                    f.write("Time(ns),Counts\n")
                    for time, count in zip(self.bins[:-1], self.hist_data):
                        f.write(f"{time},{count}\n")

            self.logger.log(f"Гистограмма сохранена в {filename}", "Info", "save_histogram")

        except Exception as e:
            self.logger.log(f"Ошибка при сохранении: {str(e)}", "Error", "save_histogram")

    def load_histogram(self):
        """Загружает гистограмму из файла"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить гистограмму",
            "",
            "CSV Files (*.csv);;NPZ Files (*.npz);;Text Files (*.txt);;All Files (*)"
        )

        if not filename:
            return

        try:
            if filename.endswith('.npz'):
                # Загрузка из бинарного формата NumPy
                data = np.load(filename)
                self.bins = data['bins']
                self.hist_data = data['hist_data']
                self.tau_max_ns = float(data['tau_max_ns'])
                self.bin_width_ns = float(data['bin_width_ns'])
            else:
                # Загрузка из текстового/CSV формата
                if filename.endswith('.csv'):
                    import csv
                    with open(filename, 'r') as f:
                        reader = csv.reader(f)
                        next(reader)  # Пропускаем заголовок
                        data = list(reader)
                else:
                    with open(filename, 'r') as f:
                        lines = f.readlines()[2:]  # Пропускаем первые две строки с параметрами
                        data = [line.strip().split(',') for line in lines]

                # Преобразуем данные в массивы
                times = []
                counts = []
                for row in data:
                    if len(row) >= 2:
                        times.append(float(row[0]))
                        counts.append(float(row[1]))

                self.hist_data = np.array(counts)
                self.bins = np.linspace(
                    min(times),
                    max(times) + (times[1] - times[0]),
                    len(times) + 1
                )
                self.tau_max_ns = max(abs(min(times)), abs(max(times)))
                self.bin_width_ns = times[1] - times[0]

            # Обновляем график
            self.plot_widget.clear()
            self.plot_widget.plot(
                self.bins,
                self.hist_data,
                stepMode=True,
                fillLevel=0,
                pen='r'
            )

            self.logger.log(f"Гистограмма загружена из {filename}", "Info", "load_histogram")

        except Exception as e:
            self.logger.log(f"Ошибка при загрузке: {str(e)}", "Error", "load_histogram")

    def closeEvent(self, event):
        self.sniff_thread.terminate()
        super().closeEvent(event)
