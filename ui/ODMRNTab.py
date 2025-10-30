import pcapy
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from Tests.utils import to_dict


class SniffThread(QThread):
    packet_signal = pyqtSignal(dict)

    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.running = True

    def run(self):
        def handle_packet(hdr, packet):
            raw_data = packet[42:]
            raw_data = to_dict(raw_data)
            #print(raw_data)
            if raw_data["flag_valid"] == 1 and (raw_data["flag_pos"] == 1 or raw_data["flag_neg"] == 1):
               self.packet_signal.emit(raw_data)
        try:
            devs = pcapy.findalldevs()
            iface = devs[6]
            cap = pcapy.open_live(iface, 106, 0, 0)
            cap.setfilter("udp and src host 192.168.1.2")
            cap.loop(0, handle_packet)

        except Exception as e:
            self.logger.log(f"{e}", "Error", "SniffThread")

    def stop(self):
        self.running = False
        self.quit()

class ODMRNTab(QWidget):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        self.sniff_thread = SniffThread(self.logger)
        self.sniff_thread.packet_signal.connect(self.process_packet)
        self.sniff_thread.start()

    def process_packet(self, packet):
        #print(packet)
        pass

