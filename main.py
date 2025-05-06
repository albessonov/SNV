from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget
from QtLogger import QtLogger

from ui.CorrelationTab import CorrelationTab
from ui.PhotonCounterWindow import PhotonCounterWindow
from ui.ImpulseTab import ImpulseTab
from ui.MappingTab import MappingTab
from ui.MirrorsControlWindow import MirrorsControlWindow

from ui.ODMRTab import ODMRTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mirrors_control = None
        self.photon_counter = None

        self.setWindowTitle("ΣNV")
        self.setWindowIcon(QIcon("assets/icon.png"))

        layout = QVBoxLayout()

        self.logger = QtLogger()
        self.logger.start()
        self.logger.setMaximumHeight(72)

        tabs = QTabWidget()
        correlation_tab = CorrelationTab(self.logger)
        odmr_tab = ODMRTab(self.logger)
        mapping_tab = MappingTab(self.logger)
        impulse_tab = ImpulseTab(self.logger)

        tabs.addTab(correlation_tab, "Корреляция")
        tabs.addTab(odmr_tab, "ОДМР")
        tabs.addTab(mapping_tab, "Картирование")
        tabs.addTab(impulse_tab, "Конструктор импульсов")

        open_mirrors_control = QPushButton("Управление зеркалами")
        open_mirrors_control.clicked.connect(self.open_mirrors_control_clicked)

        open_photon_counter = QPushButton("Счётчик фотонов")
        open_photon_counter.clicked.connect(self.open_photon_counter_clicked)

        layout.addWidget(tabs)
        layout.addWidget(self.logger)
        layout.addWidget(open_mirrors_control)
        layout.addWidget(open_photon_counter)

        central_widget = QWidget()

        central_widget.setLayout(layout)

        self.setCentralWidget(central_widget)

    def open_mirrors_control_clicked(self):
        self.mirrors_control = MirrorsControlWindow(self.logger)
        self.mirrors_control.show()

    def open_photon_counter_clicked(self):
        self.photon_counter = PhotonCounterWindow(self.logger)
        self.photon_counter.show()



if __name__ == '__main__':
    QCoreApplication.setApplicationName("ΣNV")
    QCoreApplication.setOrganizationDomain("NANOCENTER")
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
