import struct

import numpy as np
from PyQt6.QtCore import pyqtSignal, QThread, QMutex
from PyQt6.QtGui import QIntValidator, QDoubleValidator
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QProgressBar, QHBoxLayout, QPushButton, QGridLayout, QLabel, \
    QLineEdit, QFileDialog, QMessageBox, QSpinBox, QCheckBox
from matplotlib.backends.backend_qt import NavigationToolbar2QT
from numpy import arange
from pyvisa import ResourceManager
import pcapy
from hardware.rigol_rw import setup
from hardware.spincore import impulse_builder
from ui.CorrelationTab import MplCanvas


class SniffThread(QThread):
    packet_signal = pyqtSignal(dict)

    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.running = True
        self.cap = None
    def run(self):
        try:
            '''self.cap = pcapy.open_live("Device\\NPF_Loopback", 96, 0, 0) #106
            self.cap.setfilter("udp and src host localhost")
            self.logger.log("Sniffer started on 'Ethernet'", "Info", "SniffThread")
            self.cap.loop(-1, self.packet_callback)  # 0 = бесконечно'''
            interfaces = pcapy.findalldevs()

            if not interfaces:
                print("Не найдены интерфейсы!")
                return

            # В Windows loopback интерфейс часто называется "Adapter for loopback traffic capture"
            # или содержит "loopback". Если не нашли, используем первый интерфейс.
            selected_iface = None
            for iface in interfaces:
                if 'loopback' in iface.lower() or '127.0.0.1' in iface:
                    selected_iface = iface
                    break

            if not selected_iface:
                selected_iface = interfaces[0]
                print(f"Loopback интерфейс не найден, используем: {selected_iface}")
            else:
                print(f"Используем интерфейс: {selected_iface}")
                self.cap = pcapy.open_live(selected_iface, 65536, True, 1000)
                self.cap.setfilter("udp")
                self.cap.loop(0,self.packet_callback)
        except Exception as e:
            self.logger.log(f"Sniffer error: {e}", "Error", "SniffThread")

    def packet_callback(self, header, packet):
        """Обработка каждого пакета"""
        self.logger.log(f"Enter", "Error", "PacketCallback")
        if not self.running:
            return

        try:
            # Берем полезную нагрузку после 42 байт заголовков Ethernet/IP/UDP
            print("got packet")

            payload = packet[32:] #42
            if len(payload) != 64:
                self.logger.log(f"Wrong packet len", "Error", "PacketCallback")

            # Разбор байт пакета
            package_id = struct.unpack('<H', payload[1:3])[0]
            byte6 = struct.unpack('<B', payload[5:6])[0]

            flag_valid = byte6 & 0x1
            flag_pos = (byte6 & 0x10) >> 4
            flag_neg = (byte6 & 0x8) >> 3

            count_pos = int.from_bytes(payload[58:61], byteorder="little")
            count_neg = int.from_bytes(payload[61:63], byteorder="little")

            result = {
                "package_id": package_id,
                "flag_valid": flag_valid,
                "flag_neg": flag_neg,
                "flag_pos": flag_pos,
                "count_neg": count_neg,
                "count_pos": count_pos
            }

            # Отправляем только валидные пакеты
            if flag_valid == 1 and (flag_pos == 1 or flag_neg == 1):
                self.packet_signal.emit(result)

        except Exception as e:
            self.logger.log(f"Packet processing error: {e}", "Error", "SniffThread")

    def stop(self):
        """Остановка захвата"""
        self.running = False
        try:
            if self.cap:
                # Прерываем cap.loop()
                self.cap.breakloop()
                self.logger.log("Sniffer stopped", "Info", "SniffThread")
        except Exception as e:
            self.logger.log(f"Error stopping sniffer: {e}", "Error", "SniffThread")
        self.quit()


class DataProcessingThread(QThread):
    data_updated = pyqtSignal(np.ndarray)

    def __init__(self, num_points, logger):
        super().__init__()
        self.num_points = num_points
        self.logger = logger
        self.data = []
        self.running = True
        self.reset_data()

    def reset_data(self):
        self.data = np.zeros(self.num_points)

    def add_data_point(self, index, count_pos):
        try:
            if index < self.num_points:
                self.data[index] += count_pos
                self.data_updated.emit(self.data)

        except Exception as e:
            self.logger.log(f"Data processing error: {str(e)}", "Error", "DataProcessingThread")

    def stop(self):
        self.running = False
        self.quit()

class PlotUpdater(QThread):
    def __init__(self, canvas, plot_line, frequencies):
        super(PlotUpdater, self).__init__()
        self.canvas = canvas
        self.plot_line = plot_line
        self.frequencies = frequencies
        self.ratio = None
        self.increment_sweep = 0
        self.needs_update = False
    
    def update_data(self, ratio, increment_sweep):
        self.ratio = ratio
        self.increment_sweep = increment_sweep
        self.needs_update = True
    
    def run(self):
        while 1:
            if self.ratio is not None and self.needs_update:
                x_data = self.frequencies / 1e6
                y_data = self.ratio / (self.increment_sweep + 1)
                self.plot_line.set_data(x_data, y_data)
                self.canvas.axes.set_title(f"Итерация: {self.increment_sweep + 1}")
                self.canvas.axes.relim()
                self.canvas.axes.autoscale_view()
                self.canvas.draw()
            self.msleep(30)



class ODMRTab(QWidget):
    def __init__(self, logger):
        super().__init__()
        self.logger = logger
        self.frequencies = np.array([])
        self.measurement_running = False
        self.sniff_thread = None
        self.data_thread = None
        self.current_point = 0
        self.num_points = 0
        self.impulse_config = None
        self.increment_sweep = 0

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("%p% | ?/?")
        self.progress_bar.setValue(0)

        # Control buttons
        control_layout = QHBoxLayout()
        self.measurement_button = QPushButton('Старт')
        self.measurement_button.clicked.connect(self.toggle_measurement)
        self.load_impulse_button = QPushButton('Загрузить конфигурацию импульсов')
        self.load_impulse_button.clicked.connect(self.load_impulse_config)

        control_layout.addWidget(self.measurement_button)
        control_layout.addWidget(self.load_impulse_button)

        # Frequency parameters
        params_layout = QGridLayout()

        labels = [
            "Начальная частота, MГц", "Шаг частоты, Гц",
            "Выходная мощность, дБм", "Конечная частота, MГц"
        ]

        self.frequency_start_edit = QLineEdit()
        self.frequency_step_edit = QLineEdit()
        self.output_power_edit = QLineEdit()
        self.frequency_stop_edit = QLineEdit()

        fields = [
            self.frequency_start_edit, self.frequency_step_edit,
            self.output_power_edit, self.frequency_stop_edit
        ]

        for field in fields:
            field.setValidator(QDoubleValidator())

        # Layout parameters
        for i, label in enumerate(labels):
            params_layout.addWidget(QLabel(label), i, 0)

        params_layout.addWidget(self.frequency_start_edit, 0, 1)
        params_layout.addWidget(self.frequency_step_edit, 1, 1)
        params_layout.addWidget(self.output_power_edit, 2, 1)
        params_layout.addWidget(self.frequency_stop_edit, 3, 1)

        # Plot
        self.canvas = MplCanvas(self, width=5, height=4, dpi=90)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        # Assemble main layout
        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.canvas)
        main_layout.addWidget(self.progress_bar)
        main_layout.addLayout(control_layout)
        main_layout.addLayout(params_layout)

        self.setLayout(main_layout)

        # Initialize plot
        self.canvas.axes.set_xlabel('Частота (MHz)')
        self.canvas.axes.set_ylabel('Количество фотонов')
        self.plot_line, = self.canvas.axes.plot([], [], 'b-')
        self.canvas.draw()

        self.plot_thread = None
        RES = "USB0::0x1AB1::0x099C::DSG3G264300050::INSTR"
        #self.rm = ResourceManager()

    def generate_frequencies(self):
        try:
            start = float(self.frequency_start_edit.text()) * 1e6  # MHz to Hz
            stop = float(self.frequency_stop_edit.text()) * 1e6  # MHz to Hz
            step = float(self.frequency_step_edit.text())  # Hz

            if start >= stop:
                raise ValueError("Start frequency must be less than stop frequency")
            if step <= 0:
                raise ValueError("Step must be positive")

            self.frequencies = np.arange(start=start, stop=(stop+step), step=step)
            self.num_points = len(self.frequencies)
            self.progress_bar.setMaximum(self.num_points)
            return True

        except ValueError as e:
            self.logger.log(f"Frequency generation error: {e}", "Error", "ODMRTab")
            return False

    def load_impulse_config(self):
        """Загружает конфигурацию импульсов из файла"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Загрузить конфигурацию импульсов",
            "",
            "Pulse Config Files (*.pcfg);;All Files (*)"
        )
        if not filename:
            return False

        try:
            with open(filename, 'r') as f:
                content = f.read().strip()

            # Удаляем внешние скобки если они есть
            if content.startswith('(') and content.endswith(')'):
                content = content[1:-1].strip()

            # Разбиваем строку на элементы
            elements = []
            current = ""
            in_list = False
            for char in content:
                if char == '[':
                    in_list = True
                    current += char
                elif char == ']':
                    in_list = False
                    current += char
                elif char == ',' and not in_list:
                    elements.append(current.strip())
                    current = ""
                else:
                    current += char
            elements.append(current.strip())

            # Проверяем минимальное количество элементов
            if len(elements) < 5:
                raise ValueError("Недостаточно параметров в файле (требуется минимум 5)")

            # Функция для безопасного парсинга списков
            def parse_list(s):
                s = s.strip()
                if not (s.startswith('[') and s.endswith(']')):
                    raise ValueError(f"Ожидается список в квадратных скобках: {s}")
                return [int(item.strip()) for item in s[1:-1].split(',') if item.strip()]

            # Основные параметры
            num_channels = int(elements[0])
            channels = parse_list(elements[1])
            counts = parse_list(elements[2])
            starts = parse_list(elements[3])
            stops = parse_list(elements[4])

            # Проверяем согласованность данных
            if len(channels) != len(counts):
                raise ValueError("Количество каналов не совпадает с количеством счетчиков")

            total_pulses = sum(counts)
            if len(starts) != total_pulses or len(stops) != total_pulses:
                raise ValueError("Количество стартов/стопов не соответствует количеству импульсов")
            
            pulse_scale_raw = int(elements[6].strip() if len(elements) > 6 else "1")

            if pulse_scale_raw == 0:
                pulse_scale_0 = 1
            elif pulse_scale_raw == 1:
                pulse_scale_0 = 1E3
            elif pulse_scale_raw == 2:
                pulse_scale_0 = 1E6
            
            rep_scale_raw = int(elements[7].strip() if len(elements) > 7 else "1")

            if rep_scale_raw == 0:
                rep_scale_0 = 1
            elif rep_scale_raw == 1:
                rep_scale_0 = 1E3
            elif rep_scale_raw == 2:
                rep_scale_0 = 1E6


            # Сохраняем конфигурацию
            self.impulse_config = {
                'num_channels': num_channels,
                'channels': channels,
                'counts': counts,
                'starts': starts,
                'stops': stops,
                'repeat_time': elements[5].strip() if len(elements) > 5 else "10",
                'pulse_scale': pulse_scale_0,
                'rep_scale': rep_scale_0
            }

            self.logger.log(f"Конфигурация импульсов загружена из {filename}", "Info", "load_impulse_config")
            return True

        except Exception as e:
            error_msg = f"Ошибка при загрузке: {str(e)}"
            self.logger.log(error_msg, "Error", "load_impulse_config")
            return False

    def validate_inputs(self):
        try:
            if not all([self.frequency_start_edit.text(),
                        self.frequency_stop_edit.text(),
                        self.frequency_step_edit.text(),
                        self.output_power_edit.text()]):
                self.logger.log("Not all parameters are filled", "Error", "ODMRTab")
                return False

            gain = float(self.output_power_edit.text())
            if not (-110 <= gain <= 0):
                self.logger.log("Power must be between -20 and 20 dBm", "Error", "ODMRTab")
                return False

            if not self.impulse_config:
                self.logger.log("No impulse configuration loaded", "Error", "ODMRTab")
                return False

            return True
        except ValueError:
            self.logger.log("Invalid parameter values", "Error", "ODMRTab")
            return False

    def setup_devices(self):
        gain = int(self.output_power_edit.text())
        start_freq = float(self.frequency_start_edit.text()) * 1e6
        stop_freq = float(self.frequency_stop_edit.text()) * 1e6
        step_freq = float(self.frequency_step_edit.text())

        setup(gain, start_freq, stop_freq, step_freq, self.logger)

        return True

    def toggle_measurement(self):
        if self.measurement_running:
            self.stop_measurement()
        else:
            self.start_measurement()

    def start_measurement(self):
        if not self.validate_inputs() or not self.generate_frequencies():
            return
        
        if not self.setup_devices():
            return
        
        RES = "USB0::0x1AB1::0x099C::DSG3G264300050::INSTR"
        self.dev = self.rm.open_resource(RES)
        
        self.sniff_thread = SniffThread(self.logger)
        self.sniff_thread.packet_signal.connect(self.process_packet)
        self.sniff_thread.start()

        reply = QMessageBox.question(
            self, ' ', "Переведите тумблер на SpinCore ↑.\nПосле этого нажмите OK",
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )

        if reply != QMessageBox.StandardButton.Ok:
            return  

        # Загружаем конфигурацию импульсов после подтверждения
        try:
            # Проверяем, что конфигурация загружена
            if not self.impulse_config:
                self.logger.log("No impulse configuration loaded", "Error", "ODMRTab")
                return False

            # Запускаем импульсную последовательность
            impulse_builder(
                self.impulse_config['num_channels'],
                self.impulse_config['channels'],
                self.impulse_config['counts'],
                self.impulse_config['starts'],
                self.impulse_config['stops'],
                int(self.impulse_config['repeat_time']),
                int(self.impulse_config['pulse_scale']),
                int(self.impulse_config['rep_scale'])
            )
        except Exception as e:
            self.logger.log(f"Error starting impulse sequence: {str(e)}", "Error", "ODMRTab")
            return False

        # Start data processing thread
        self.data_thread = DataProcessingThread(
            self.num_points,
            self.logger
        )
        self.data_thread.data_updated.connect(self.update_plot)
        self.data_thread.start()

        self.measurement_running = True
        self.current_point = 0

        self.measurement_button.setText("Стоп")
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(f"0% | 0/{self.num_points}")

        # Clear plot
        self.canvas.axes.clear()
        self.plot_line, = self.canvas.axes.plot([], [], 'b-')
        self.canvas.axes.set_xlabel('Частота (MHz)')
        self.canvas.axes.set_ylabel('Сигнал')

        
    def stop_measurement(self):
        self.measurement_running = False
        self.measurement_button.setText("Старт")

        if self.sniff_thread:
            self.sniff_thread.stop()
            self.sniff_thread.wait()
            self.sniff_thread = None

        if self.data_thread:
            self.data_thread.stop()
            self.data_thread.wait()
            self.data_thread = None

    def process_packet(self, packet):
        if not self.measurement_running:
            return

        if packet['flag_pos'] == 1:

            if self.current_point == 0 or self.current_point+1 == self.num_points:
                print(self.increment_sweep,self.dev.query(":FREQ?"))
            
            count_pos = packet['count_pos']
            self.data_thread.add_data_point(self.current_point, count_pos)

           
            #self.progress_bar.setValue(self.current_point)
            """self.progress_bar.setFormat(
                f"{int(100 * self.current_point / self.num_points)}% | "
                f"{self.current_point}/{self.num_points} |"
                f"Проход: {self.increment_sweep + 1}"
            )"""

            #print((time.process_time_ns()-t)*1E-6, self.current_point)

            if self.current_point == self.num_points:
                self.increment_sweep += 1
                self.current_point = 0
            else:
                self.current_point += 1
           
    def update_plot(self, ratio):
        if self.plot_thread is None:
            self.plot_thread = PlotUpdater(
            self.canvas,
            self.plot_line,
            self.frequencies
        )
            self.plot_thread.start()
        else:
            self.plot_thread.update_data(ratio, self.increment_sweep)


    def closeEvent(self, event):
        self.stop_measurement()
        super().closeEvent(event)
