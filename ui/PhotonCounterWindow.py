from collections import deque

from PyQt6.QtWidgets import QWidget

from ui.CorrelationTab import MplCanvas, SniffThread, CounterWorker


class PhotonCounterWindow(QWidget):
    def __init__(self, logger):
        super().__init__()
        self.plot_thread = None
        self.init = False
        self.logger = logger
        self.photon_data = deque(maxlen=10000)
        self.canvas = MplCanvas(self, width=5, height=4, dpi=90)
        self.sniff_thread = SniffThread(self.logger)
        self.sniff_thread.packet_signal.connect(self.packet_received)
        self.sniff_thread.start()

    def packet_received(self, packet):
        if not self.init and packet['flag']:
            # Инициализация при первом флаговом пакете
            self.plot_thread = CounterWorker(self.canvas, self.photon_data)
            self.plot_thread.start()

    def closeEvent(self, event):
        self.sniff_thread.terminate()
        super().closeEvent(event)

