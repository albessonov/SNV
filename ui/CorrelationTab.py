import time

import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtMultimedia import QSoundEffect
import struct
from PyQt6.QtCore import QThread, pyqtSignal
from numpy import correlate
from scapy.all import sniff


class SniffThread(QThread):
    packet_signal = pyqtSignal(dict)

    def __init__(self, logger):
        super().__init__()
        self.logger = logger

    def run(self):
        # Функция обратного вызова для обработки каждого пакета
        def packet_callback(packet):
            if packet.haslayer("IP") and packet.haslayer("UDP"):
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
                    # print("a",tp1_r)

                    tp2 = [int.from_bytes(payload[34 + 4 * i:38 + 4 * i], byteorder="little") for i in range(0, 5 + 1)]
                    tp2_a = [np.round((tp2[i] & 0x1F) * 0.18, 1) for i in range(len(tp2))]  # ns
                    tp2_b = [np.round((tp2[i] >> 7) * 5, 1) for i in range(len(tp2))]  # ns
                    tp2_r = [(tp2_a[i] + tp2_b[i]) for i in range(len(tp2_a))]  # ns
                    # print("b", tp2_r)

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
            sniff(iface="Ethernet", filter="udp and src host 192.168.1.2", prn=packet_callback, count=0)
        except Exception as e:
            self.logger.log(f"{e}", "Error", "SniffThread")


def cross_correlation(timestamps1, timestamps2, bin_size=1.0):
    """
    Вычисляет кросс-корреляцию между двумя наборами временных меток
    с возможностью визуализации.

    Параметры:
    timestamps1 (array): Временные метки первого детектора (в нс)
    timestamps2 (array): Временные метки второго детектора (в нс)
    bin_size (float): Размер бина в наносекундах

    Возвращает:
    lags (array): Массив временных задержек
    correlation (array): Нормированные значения корреляции
    """
    # Создаем общий временной диапазон
    start_time = min(min(timestamps1), min(timestamps2))
    end_time = max(max(timestamps1), max(timestamps2))

    # Создаем временные оси с выбранным бином
    time_axis = np.arange(start_time, end_time + bin_size, bin_size)

    # Создаем гистограммы
    hist1, _ = np.histogram(timestamps1, bins=time_axis)
    hist2, _ = np.histogram(timestamps2, bins=time_axis)

    # Вычисляем кросс-корреляцию
    correlation = np.correlate(hist1, hist2, mode='full')

    # Рассчитываем временные задержки
    lags = np.arange(-len(hist2) + 1, len(hist1)) * bin_size

    # Нормализация
    norm = (len(timestamps1) * len(timestamps2) * bin_size) / (end_time - start_time)
    correlation = correlation / norm if norm != 0 else correlation

    return lags, correlation


class CorrelationTab(QWidget):
    def __init__(self, logger):
        super().__init__()
        self.photon_data = []
        self.init = False
        self.logger = logger

        layout = QVBoxLayout()
        self.canvas = FigureCanvas(plt.figure())
        layout.addWidget(self.canvas)
        self.sniff_thread = SniffThread(self.logger)
        self.sniff_thread.packet_signal.connect(self.packet_received)
        self.sniff_thread.start()
        self.setLayout(layout)

    def packet_received(self, packet):
        if packet['flag'] and not self.init:
            self.logger.log("Init", "info", "packet_received")
            self.init = True
            self.photon_data.append(packet)
        elif not packet['flag'] and self.init:
            self.photon_data.append(packet)
        elif packet['flag'] and self.init:
            # Собрали полный период
            self.logger.log("Собрали полный период", "info", "packet_received")

            tau_max_ns = 100  # 100 нс
            bin_width_ns = 1
            num_bins = int(np.round(tau_max_ns / bin_width_ns))
            bins = np.linspace(-tau_max_ns, tau_max_ns, num_bins + 1)

            all_t1 = [self.photon_data[i]["tp1_r"] for i in range(len(self.photon_data))]
            all_t2 = [self.photon_data[i]["tp2_r"] for i in range(len(self.photon_data))]


            # Проверка, что метки не превышают tau_max_ns
            all_t1 = [t[(t > 0)] for t in all_t1]
            all_t2 = [t[(t > 0)] for t in all_t2]

            # Предварительный расчет гистограммы
            hist = np.zeros(len(bins) - 1, dtype=np.int64)

            for t1, t2 in zip(all_t1, all_t2):
                # Векторизованный расчет всех разниц
                delta = t1[:, None] - t2  # Создает матрицу разниц
                # Фильтрация за один шаг
                mask = (delta > -tau_max_ns) & (delta < tau_max_ns)
                valid_deltas = delta[mask]

                # Прямое добавление в гистограмму
                if valid_deltas.size > 0:
                    hist += np.histogram(valid_deltas, bins=bins)[0]

            bin_edges = bins

            # Очищаем текущий график, чтобы предотвратить наложение осей
            self.canvas.figure.clf()  # Полностью очищаем текущую фигуру

            # Создаем новый subplot
            ax = self.canvas.figure.add_subplot(111)
            ax.bar(bin_edges[:-1], hist)
            ax.set_title("Случайный график")
            ax.set_xlabel('Задержка τ, нс')
            ax.set_ylabel('g²(τ)')
            ax.set_xlim(-tau_max_ns * 1.05, tau_max_ns * 1.05)

            # Перерисовываем график
            self.canvas.draw()


            self.sound = QSoundEffect(self)
            self.sound.setSource(QUrl.fromLocalFile(r"C:\Users\verrg\Projects\SNV\assets\finished.wav"))

            self.sound.play()
