import sys

from PyQt6.QtCore import QCoreApplication
from PyQt6.QtGui import QIcon
from QtLogger import QtLogger

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTabWidget, QLabel

from hardware import mirrors
from ui.MapTab import MapTab, MapTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ΣNV")
        self.setWindowIcon(QIcon("assets/icon.png"))

        layout = QVBoxLayout()

        self.logger = QtLogger()
        self.logger.start()
        self.logger.setMaximumHeight(72)

        tabs = QTabWidget()
        map_tab = MapTab(self.logger)
        tabs.addTab(map_tab, "Картирование")

        layout.addWidget(tabs)
        layout.addWidget(self.logger)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

if __name__ == '__main__':
    QCoreApplication.setApplicationName("ΣNV")
    QCoreApplication.setOrganizationDomain("NANOCENTER")
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
