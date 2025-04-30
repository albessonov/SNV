import struct

import numpy as np
from PyQt6.QtCore import pyqtSignal, QThread
from PyQt6.QtWidgets import QVBoxLayout, QWidget
from matplotlib.backends.backend_qt import NavigationToolbar2QT
from numpy import arange
from pyvisa import ResourceManager
from scapy.sendrecv import sniff

from hardware.spincore import impulse_builder
from ui.CorrelationTab import MplCanvas

RES = "USB0::0x1AB1::0x099C::DSG3G264300050::INSTR"


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
                    return

                try:
                    package_id = struct.unpack('<H', payload[1:3])[0]

                    # Распаковка данных
                    byte6 = struct.unpack('<B', payload[5:6])[0]

                    flag_valid = byte6 & 0x1

                    flag_pos = (byte6 & 0x10) >> 4
                    flag_neg = (byte6 & 0x8) >> 3

                    count_pos = int.from_bytes(payload[58:59], byteorder="little")
                    count_neg = int.from_bytes(payload[60:61], byteorder="little")

                    # Создаем словарь с результатами
                    result = {
                        "package_id": package_id,
                        "flag_valid": flag_valid,
                        "flag_neg": flag_neg,
                        "flag_pos": flag_pos,
                        "count_neg": count_neg,
                        "count_pos": count_pos

                    }
                    print(result['flag_valid'])
                    if flag_valid == 1:
                        # Отправляем данные через сигнал
                        if flag_pos == 1:
                            #print(payload[58:59])
                            self.packet_signal.emit(result)
                except Exception:
                    pass

        try:
            sniff(iface="Ethernet", filter="src host 192.168.1.2", prn=packet_callback, count=0)
        except Exception as e:
            self.logger.log(f"{e}", "Error", "SniffThread")

class AveragingThread(QThread):
    pass



class CanvasThread(QThread):
    def __init__(self, *args):
        super(CanvasThread, self).__init__()
        self.logger = args[0]
        self.canvas = args[1]
        self.freq = args[2]
        self.ph = args[3]

    def run(self):
        self.canvas.axes.plot(self.freq, self.ph[-1])
        self.canvas.axes.set_xlabel('Частота')
        self.canvas.axes.set_ylabel('Фотоны')
        self.canvas.draw()
        self.canvas.flush_events()


def setup(gain: int, start_freq: float, stop_freq: float, step_freq: float):
    """
    Args:
        gain: усиление, [дБм]
        start_freq: начальная частота, [Гц]
        stop_freq: конечная частота, [Гц]
        step_freq: шаг частоты, [Гц]
    """
    if 9 * 1E3 <= start_freq <= 13.6 * 1E9 and 9 * 1E3 <= stop_freq <= 13.6 * 1E9:
        rm = ResourceManager()
        dev = rm.open_resource(RES)

        points_number = np.round((stop_freq - start_freq) / step_freq, 0) + 1

        dev.write(f':LEV {gain}dBm')

        dev.write(':SOUR1:FUNC:MODE SWE')
        dev.write(":SWE:MODE CONT")
        dev.write(":SWE:STEP:SHAP RAMP")
        dev.write(":SWE:TYPE STEP")

        dev.write(f":SWE:STEP:POIN {points_number}")
        dev.write(f":SWE:STEP:STAR:FREQ {start_freq}")
        dev.write(f":SWE:STEP:STOP:FREQ {stop_freq}")

        dev.write("SWE:POIN:TRIG:TYPE EXT")

        dev.write(":OUTP 1")

        dev.close()
    else:
        raise ValueError("Превышен диапазон")


class ODMRTab(QWidget):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.freq = arange(start=2.83 * 1E9, stop=2.9 * 1E9 + 1, step=500 * 1E3)
        self.resq = []
        self.tem = []

        # Основной вертикальный layout
        main_layout = QVBoxLayout(self)

        # Виджеты для графика
        self.canvas = MplCanvas(self, width=5, height=4, dpi=90)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # Добавляем toolbar без stretch factor
        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.canvas)

        self.setLayout(main_layout)

        setup(-20, 2.83 * 1E9, 2.9 * 1E9, 500 * 1E3)
        input("Включи. Теперь enter")
        print("Поехали !")
        impulse_builder(3, [0, 1, 2], [1, 1, 1], [0, 10, 0], [10, 20, 10], 10, 1000000, 1)

        self.sniff_thread = SniffThread(self.logger)
        self.sniff_thread.packet_signal.connect(self.packet_received)
        self.sniff_thread.start()

    def packet_received(self, packet):
        if len(self.tem) < 141:
            self.tem.append(packet["count_pos"])
        else:
            self.canvas.axes.clear()
            self.canvas.axes.cla()
            self.resq.append(self.tem)
            self.tem = []
            self.canvas_thread = CanvasThread(self.logger, self.canvas, self.freq, self.resq)
            self.canvas_thread.start()
