import struct
import time
from collections import deque

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from fast_histogram import histogram1d
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from scapy.compat import raw
from scapy.layers.l2 import Ether
from scapy.sendrecv import sniff

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
        self.y_data = np.zeros(self.window_size)
        self.line, = self.canvas.axes.plot(self.x_data, self.y_data, lw=2)
        self.canvas.axes.set_xlabel('Время')
        self.canvas.axes.set_ylabel('Отсчеты')
        self.canvas.axes.grid()
        self.is_killed = False

    def run(self):
        while not self.is_killed:
            try:
                data_point = self.photon_data[-1]['cnt_photon_1']
                print(self.photon_data[-1]['cnt_photon_2'])
            except Exception:
                data_point = 0
            time.sleep(1)
            self.y_data = np.roll(self.y_data, -1)
            self.y_data[-1] = data_point

            max_data = np.max(self.y_data)
            min_data = np.min(self.y_data)
            self.canvas.axes.set_xlim(0, 100)
            self.canvas.axes.set_ylim(min_data, max_data + 5)
            self.line.set_ydata(self.y_data)
            self.canvas.draw()
            self.canvas.flush_events()

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
        deltas = np.hstack([t1[:, None] - t2 for t1, t2 in self.data])
        valid = deltas[(deltas > -self.tau_max_ns) & (deltas < self.tau_max_ns)]
        hist = histogram1d(valid, bins=len(self.bins) - 1, range=(-self.tau_max_ns, self.tau_max_ns))

        self.result_ready.emit(hist)


class SniffThread(QThread):
    packet_signal = pyqtSignal(dict)

    def __init__(self, logger):
        super().__init__()
        self.logger = logger

    def run(self):
        # Функция обратного вызова для обработки каждого пакета
        def packet_callback(packet):
            if packet.haslayer("Raw"):
                payload = bytes(packet["Raw"].load)[28:]

                # Защита от неверного размера
                if len(payload) < 58:
                    self.logger.log(f"Некорректный размер пакета", "Error", "packet_callback")
                    return

                try:
                    # Распаковка данных
                    package_id = struct.unpack('<H', payload[1:3])[0]
                    byte6 = struct.unpack('<B', payload[5:6])[0]
                    flag = (byte6 >> 7) & 1
                    cnt_photon_1 = struct.unpack('<H', payload[6:8])[0]
                    cnt_photon_2 = struct.unpack('<H', payload[8:10])[0]

                    tp1 = [int.from_bytes(payload[10 + 4 * i:14 + 4 * i], byteorder="little") for i in range(0, 5 + 1)]
                    tp1_a = [np.round((tp1[i] & 0x1F) * 0.18, 1) for i in range(len(tp1))]  # ns
                    tp1_b = [np.round((tp1[i] >> 7) * 5, 1) for i in range(len(tp1))]  # ns
                    tp1_r = [(tp1_a[i] + tp1_b[i]) for i in range(len(tp1_a))]  # ns

                    tp2 = [int.from_bytes(payload[34 + 4 * i:38 + 4 * i], byteorder="little") for i in range(0, 5 + 1)]
                    tp2_a = [np.round((tp2[i] & 0x1F) * 0.18, 1) for i in range(len(tp2))]  # ns
                    tp2_b = [np.round((tp2[i] >> 7) * 5, 1) for i in range(len(tp2))]  # ns
                    tp2_r = [(tp2_a[i] + tp2_b[i]) for i in range(len(tp2_a))]  # ns

                    # Создаем словарь с результатами
                    # FIXME Есть определённая избыточность в получаемых данных, стоит разделить на два метода: один чисто для счёта фотонов, другой для корелляции
                    result = {
                        "package_id": package_id,
                        "flag": flag,
                        "cnt_photon_1": cnt_photon_1,
                        "cnt_photon_2": cnt_photon_2,
                        "tp1_r": np.array(tp1_r),
                        "tp2_r": np.array(tp2_r)
                    }
                    #print(result)
                    # Отправляем данные через сигнал
                    self.packet_signal.emit(result)
                except Exception:
                    self.logger.log(f"Неудачный парсинг пакета", "Error", "packet_callback")


            elif packet.haslayer("IP") and packet.haslayer("UDP"):
                payload = bytes(packet["UDP"].payload)

                # Защита от неверного размера
                if len(payload) < 58:
                    self.logger.log(f"Некорректный размер пакета", "Error", "packet_callback")
                    return

                try:
                    # Распаковка данных
                    package_id = struct.unpack('<H', payload[1:3])[0]
                    byte6 = struct.unpack('<B', payload[5:6])[0]
                    flag = (byte6 >> 7) & 1
                    cnt_photon_1 = struct.unpack('<H', payload[6:8])[0]
                    cnt_photon_2 = struct.unpack('<H', payload[8:10])[0]

                    tp1 = [int.from_bytes(payload[10 + 4 * i:14 + 4 * i], byteorder="little") for i in range(0, 5 + 1)]
                    tp1_a = [np.round((tp1[i] & 0x1F) * 0.18, 1) for i in range(len(tp1))]  # ns
                    tp1_b = [np.round((tp1[i] >> 7) * 5, 1) for i in range(len(tp1))]  # ns
                    tp1_r = [(tp1_a[i] + tp1_b[i]) for i in range(len(tp1_a))]  # ns

                    tp2 = [int.from_bytes(payload[34 + 4 * i:38 + 4 * i], byteorder="little") for i in range(0, 5 + 1)]
                    tp2_a = [np.round((tp2[i] & 0x1F) * 0.18, 1) for i in range(len(tp2))]  # ns
                    tp2_b = [np.round((tp2[i] >> 7) * 5, 1) for i in range(len(tp2))]  # ns
                    tp2_r = [(tp2_a[i] + tp2_b[i]) for i in range(len(tp2_a))]  # ns

                    # Создаем словарь с результатами
                    # FIXME Есть определённая избыточность в получаемых данных, стоит разделить на два метода: один чисто для счёта фотонов, другой для корелляции
                    result = {
                        "package_id": package_id,
                        "flag": flag,
                        "cnt_photon_1": cnt_photon_1,
                        "cnt_photon_2": cnt_photon_2,
                        "tp1_r": np.array(tp1_r),
                        "tp2_r": np.array(tp2_r)
                    }
                    # Отправляем данные через сигнал
                    self.packet_signal.emit(result)
                except Exception:
                    self.logger.log(f"Неудачный парсинг пакета", "Error", "packet_callback")

        try:
             sniff(iface="Ethernet", filter="src host 192.168.1.2", prn=packet_callback, count=0)
        except Exception as e:
            self.logger.log(f"{e}", "Error", "SniffThread")


class CorrelationTab(QWidget):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.photon_data = deque(maxlen=10000)
        self.hist_data = None
        self.bins = None
        self.tau_max_ns = 100
        self.bin_width_ns = 0.001
        self.num_bins = None
        self.init = False

        layout = QVBoxLayout()

        plots_layout = QHBoxLayout()
        self.canvas = MplCanvas(self, width=5, height=4, dpi=90)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setTitle("g2", size="13pt")
        self.plot_widget.setLabel("left", "Счёты", size="13pt")
        self.plot_widget.setLabel("bottom", "Время [нс]", size="13pt")
        self.plot_widget.showGrid(x=True, y=True)

        plots_layout.addWidget(self.canvas)
        plots_layout.addWidget(self.plot_widget)

        layout.addLayout(plots_layout)
        self.setLayout(layout)

        self.sniff_thread = SniffThread(self.logger)
        self.sniff_thread.packet_signal.connect(self.packet_received)
        self.sniff_thread.start()

        self.plot_thread = CounterWorker(self.canvas, self.photon_data)
        self.plot_thread.start()

    def packet_received(self, packet):
        if not self.init and packet['flag']:
            # Инициализация при первом флаговом пакете
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

    def closeEvent(self, event):
        self.sniff_thread.terminate()
        super().closeEvent(event)
