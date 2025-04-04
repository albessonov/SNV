import struct
import asyncio
from PyQt6.QtCore import QThread, pyqtSignal
from scapy.all import sniff

class SniffThread(QThread):
    packet_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

    def run(self):
        # Используем asyncio для асинхронного выполнения в фоновом потоке
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.sniff_async())

    async def sniff_async(self):
        # Функция обратного вызова для обработки каждого пакета
        def packet_callback(packet):
            if packet.haslayer("IP") and packet.haslayer("UDP"):
                payload = bytes(packet["UDP"].payload)

                # Распаковка данных
                matcad = payload[:5]
                flags = struct.unpack("B", payload[5:6])[0]
                detector = struct.unpack("H", payload[6:8])[0]
                labels = [payload[i:i + 4].decode('utf-8', 'ignore') for i in range(8, 48, 4)]
                free = payload[48:64]

                # Создаем словарь с результатами
                result = {
                    "matcad": matcad,
                    "flags": flags,
                    "detector": detector,
                    "labels": labels,
                    "free": free
                }

                # Отправляем данные через сигнал
                self.packet_signal.emit(result)

        sniff(iface="Ethernet", filter="udp and src host 192.168.1.2", prn=packet_callback, count=0)

"""
Это в инициализции ui
self.sniff_thread = SniffThread()
        self.sniff_thread.packet_signal.connect(self.update_label)  # Подключаем слот для обновления GUI
        self.sniff_thread.start()

А это в получении данных
    def update_label(self, packet_data):
        # Обновляем GUI с данными из пакета
        matcad = packet_data.get("matcad")
        flags = packet_data.get("flags")
        detector = packet_data.get("detector")
        labels = packet_data.get("labels")
        free = packet_data.get("free")
"""