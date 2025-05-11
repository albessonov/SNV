from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, \
    QGridLayout, QLabel, QDoubleSpinBox, QComboBox

from hardware.mirrors import open_serial_port, get_position, move_to_position


class MirrorsControlWindow(QWidget):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger

        self.setWindowTitle("Управление зеркалами")
        self.setWindowIcon(QIcon("assets/icon.png"))
        self.setFixedSize(300, 300)

        self.serial_device = open_serial_port(self.logger)
        #FIXME пока это неверно
        self.current_position = get_position(self.serial_device, self.logger)
        self.center = self.current_position

        layout = QVBoxLayout()

        mirrors_layout = QGridLayout()

        coords_controller_layout = QGridLayout()

        x_coord = QLabel("Координата x")
        y_coord = QLabel("Координата y")

        x_coord.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        y_coord.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        self.x_coord_field = QDoubleSpinBox()
        self.y_coord_field = QDoubleSpinBox()

        self.x_coord_field.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.y_coord_field.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        self.x_coord_field.setDecimals(3)
        self.y_coord_field.setDecimals(3)

        self.x_coord_field.setSingleStep(0.001)
        self.y_coord_field.setSingleStep(0.001)

        x_coord_step = QLabel("Шаг x")
        y_coord_step = QLabel("Шаг y")

        x_coord_step.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        y_coord_step.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        self.x_coord_step_field = QDoubleSpinBox()
        self.y_coord_step_field = QDoubleSpinBox()

        self.x_coord_step_field.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        self.y_coord_step_field.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)

        self.x_coord_step_field.setDecimals(3)
        self.y_coord_step_field.setDecimals(3)

        self.x_coord_field.setRange(-35, 35)
        self.y_coord_field.setRange(-35, 35)

        self.x_coord_step_field.setRange(0.01, 100)
        self.x_coord_step_field.setSingleStep(0.001)
        self.y_coord_step_field.setRange(0.01, 100)
        self.y_coord_step_field.setSingleStep(0.001)

        coords_controller_layout.addWidget(x_coord, 0, 0)
        coords_controller_layout.addWidget(y_coord, 0, 1)
        coords_controller_layout.addWidget(self.x_coord_field, 1, 0)
        coords_controller_layout.addWidget(self.y_coord_field, 1, 1)
        coords_controller_layout.addWidget(x_coord_step, 4, 0)
        coords_controller_layout.addWidget(y_coord_step, 4, 1)
        coords_controller_layout.addWidget(self.x_coord_step_field, 5, 0)
        coords_controller_layout.addWidget(self.y_coord_step_field, 5, 1)

        buttons_controller_layout = QHBoxLayout()
        movement_xy_layout = QGridLayout()

        go_up_button = QPushButton("↑")
        go_left_button = QPushButton("←")
        go_right_button = QPushButton("→")
        go_center_button = QPushButton("◯")
        go_down_button = QPushButton("↓")

        go_up_button.clicked.connect(self.go_up_button_pressed)
        go_left_button.clicked.connect(self.go_left_button_pressed)
        go_right_button.clicked.connect(self.go_right_button_pressed)
        go_center_button.clicked.connect(self.go_center_button_pressed)
        go_down_button.clicked.connect(self.go_down_button_pressed)

        movement_xy_layout.addWidget(go_up_button, 0, 1)
        movement_xy_layout.addWidget(go_left_button, 1, 0)
        movement_xy_layout.addWidget(go_center_button, 1, 1)
        movement_xy_layout.addWidget(go_right_button, 1, 2)
        movement_xy_layout.addWidget(go_down_button, 2, 1)

        self.go_button = QPushButton("Установить зеркала")
        self.go_button.clicked.connect(self.go_button_pressed)

        buttons_controller_layout.addLayout(movement_xy_layout)

        layout.addLayout(mirrors_layout)
        layout.addLayout(coords_controller_layout)
        layout.addLayout(buttons_controller_layout)
        layout.addWidget(self.go_button)
        self.setLayout(layout)

        self.x_coord_field.setValue(self.center[0])
        self.y_coord_field.setValue(self.center[1])

    def go_up_button_pressed(self):
        new_y_coord = float(self.y_coord_field.value()) + float(self.y_coord_step_field.value())
        self.y_coord_field.setValue(new_y_coord)

        move_to_position(self.serial_device, self.center, [self.current_position[0], new_y_coord], self.logger)

        self.current_position = [self.current_position[0], new_y_coord]


    def go_down_button_pressed(self):
        new_y_coord = float(self.y_coord_field.value()) - float(self.y_coord_step_field.value())
        self.y_coord_field.setValue(new_y_coord)

        move_to_position(self.serial_device, self.center, [self.current_position[0], new_y_coord], self.logger)

        self.current_position = [self.current_position[0], new_y_coord]


    def go_left_button_pressed(self):
        new_x_coord = float(self.x_coord_field.value()) - float(self.x_coord_step_field.value())
        self.x_coord_field.setValue(new_x_coord)

        move_to_position(self.serial_device, self.center, [new_x_coord, self.current_position[1]], self.logger)

        self.current_position = [new_x_coord, self.current_position[1]]


    def go_right_button_pressed(self):
        new_x_coord = float(self.x_coord_field.value()) + float(self.x_coord_step_field.value())
        self.x_coord_field.setValue(new_x_coord)

        move_to_position(self.serial_device, self.center, [new_x_coord, self.current_position[1]], self.logger)

        self.current_position = [new_x_coord, self.current_position[1]]

    def go_center_button_pressed(self):
        move_to_position(self.serial_device, self.center, self.center, self.logger)
        self.x_coord_field.setValue(self.center[0])
        self.y_coord_field.setValue(self.center[1])

    def go_button_pressed(self):
        x_coord = float(self.x_coord_field.value())
        y_coord = float(self.y_coord_field.value())

        move_to_position(self.serial_device, self.center, [x_coord, y_coord], self.logger)

        self.current_position = [x_coord, y_coord]

    def closeEvent(self, event):
        self.serial_device.close()
        super().closeEvent(event)


