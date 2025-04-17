from PyQt6.QtCore import QThread, pyqtSignal, QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtMultimedia import QSoundEffect
import struct
from PyQt6.QtCore import QThread, pyqtSignal
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
                    tp1 = [struct.unpack('<I', payload[10 + 4 * i:14 + 4 * i])[0] for i in range(0, 5 + 1)]
                    tp1_1 = [(tp1[i] & 0b111111) * 5 for i in range(len(tp1))]  # ns
                    tp1_2 = [((tp1[i] >> 7) & ((1 << 25) - 1)) * 185 * 1E-3 for i in range(len(tp1))]  # ns
                    tp1_r = [round((tp1_1[i] + tp1_2[i]), 3) for i in range(len(tp1_1))]  # ns

                    tp2 = [struct.unpack('<I', payload[34 + 4 * i:38 + 4 * i])[0] for i in range(0, 5 + 1)]
                    tp2_1 = [(tp2[i] & 0b111111) * 5 for i in range(len(tp2))]  # ns
                    tp2_2 = [((tp2[i] >> 7) & ((1 << 25) - 1)) * 185 * 1E-3 for i in range(len(tp2))]  # ns
                    tp2_r = [round((tp2_1[i] + tp2_2[i]), 3) for i in range(len(tp2_1))]  # ns

                    # Создаем словарь с результатами
                    # FIXME Есть определённая избыточность в получаемых данных, стоит разделить на два метода: один чисто для счёта фотонов, другой для корелляции
                    result = {
                        "package_id": package_id,
                        "flag": flag,
                        "cnt_photon_1": cnt_photon_1,
                        "cnt_photon_2": cnt_photon_2,
                        "tp1_r": tp1_r,
                        "tp2_r": tp2_r
                    }
                    # Отправляем данные через сигнал
                    self.packet_signal.emit(result)
                except Exception:
                    self.logger.log(f"Неудачный парсинг пакета", "Error", "packet_callback")

        try:
            sniff(iface="Ethernet", filter="udp and src host 192.168.1.2", prn=packet_callback, count=0)
        except Exception as e:
            self.logger.log(f"{e}", "Error", "SniffThread")


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
            self.init = True
            self.photon_data.append(packet)
        elif not packet['flag'] and self.init:
            self.photon_data.append(packet)
        elif packet['flag'] and self.init:
            #Собрали полный период
            a = self.photon_data[0]['tp1_r']
            b = self.photon_data[0]['tp2_r']
            print(a, b)
            d = [[a[j] - b[i] for i in range(len(b))] for j in range(len(a))]
            k = [item for sublist in d for item in sublist]
            print(k)

            # Очищаем текущий график, чтобы предотвратить наложение осей
            self.canvas.figure.clf()  # Полностью очищаем текущую фигуру

            # Создаем новый subplot
            ax = self.canvas.figure.add_subplot(111)
            #ax.plot(x, y)
            ax.set_title("Случайный график")
            ax.set_xlabel("Ось X")
            ax.set_ylabel("Ось Y")

            # Перерисовываем график
            self.canvas.draw()

            self.sound = QSoundEffect(self)
            self.sound.setSource(QUrl.fromLocalFile(r"C:\Users\verrg\Projects\SNV\assets\finished.wav"))

            self.sound.play()
