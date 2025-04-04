import sys
from QtLogger import QtLogger

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.central_widget = QWidget()

        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()

        self.central_widget.setLayout(self.layout)

        self.button = QPushButton("Log something")

        self.button.clicked.connect(self.log_something)

        self.layout.addWidget(self.button)

        self.logger = QtLogger()

        self.layout.addWidget(self.logger)

        def log_something(self):
            self.logger.log("This is a log", "info")

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
