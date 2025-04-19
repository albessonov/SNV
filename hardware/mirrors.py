import time

import serial
from serial.serialwin32 import Serial

# CONSTANTS
MIRRORS_COM_PORT = 'COM9'
VOLTAGE_TO_LENGTH_X = 32.13 / 1.340
VOLTAGE_TO_LENGTH_Y = 31.46 / 0.940


def open_serial_port():
    try:
        serial_device = serial.Serial('COM9', 115200, timeout=0.01)
        if not serial_device.isOpen():
            serial_device.open()
    except serial.SerialException:
        raise IOError('Не получилось открыть serial port зеркал')
    else:
        return serial_device


def length_to_voltage(length: float, axis: str) -> float:
    """
    Переводит длину в напряжение
    Args:
        length (float): длина [мкм]
        axis (str): ось (x или y)

    Returns:
        float: напряжение [в]
    """
    if axis == 'x':
        return (1 / VOLTAGE_TO_LENGTH_X) * length
    elif axis == 'y':
        return (1 / VOLTAGE_TO_LENGTH_Y) * length


def voltage_to_length(voltage: float, axis: str) -> float:
    """
            Переводит напряжение в длину

            Args:
                voltage (float): напряжение [в]
                axis (str): ось (x или y)

            Returns:
                float: длина [мкм]
            """
    if axis == 'x':
        return VOLTAGE_TO_LENGTH_X * voltage
    elif axis == 'y':
        return VOLTAGE_TO_LENGTH_Y * voltage


def move_command(serial_device: Serial, voltage_position: [str, str]):
    """
    Отправляет команду на установку зеркал
    :param serial_device: зеркала
    :param voltage_position: [str, str] желаемая позиция в вольтах
    """
    x = float(voltage_position[0])
    y = float(voltage_position[1])
    if 0 <= x <= 3.3 and 0 <= y <= 3.3:
        x = format(x, '.3f')
        y = format(y, '.3f')
        serial_device.write(f"{x}|{y}F".encode())
    else:
        raise ValueError("Запрещённый диапазон напряжения")


def move_to_position(serial_device: Serial, center: [float, float], position: [float, float]):
    """
    Перемещает зеркала в необходимую точку на плоскости
    :param serial_device: зеркала
    :param center: [float, float] позиция центра СК в длинах
    :param position: [float, float] желаемая позиция относительно центра СК в длинах
    """
    x_center_voltage, y_center_voltage = None, None
    if center[0] >= 0:
        x_center_voltage = 1.650 - length_to_voltage(center[0], 'x')
    elif center[0] < 0:
        x_center_voltage = 1.650 + length_to_voltage(abs(center[0]), 'x')

    if center[1] >= 0:
        y_center_voltage = 1.650 - length_to_voltage(center[1], 'y')
    elif center[1] < 0:
        y_center_voltage = 1.650 + length_to_voltage(abs(center[1]), 'y')

    if not (0 <= x_center_voltage <= 3.3 and 0 <= y_center_voltage <= 3.3):
        raise ValueError("Запрещённое значение напряжения для центра СК")

    x_voltage, y_voltage = None, None
    if position[0] >= center[0]:
        x_voltage = format(x_center_voltage - length_to_voltage(position[0], 'x'), '.3f')
    elif position[0] < center[0]:
        x_voltage = format(x_center_voltage + length_to_voltage(abs(position[0]), 'x'), '.3f')

    if position[1] >= center[1]:
        y_voltage = format(y_center_voltage - length_to_voltage(position[1], 'y'), '.3f')
    elif position[1] < center[1]:
        y_voltage = format(y_center_voltage + length_to_voltage(abs(position[1]), 'y'), '.3f')

    if not (0 <= float(x_voltage) <= 3.3 and 0 <= float(y_voltage) <= 3.3):
        raise ValueError("Запрещённое значение напряжения для точки установки зеркал")

    move_command(serial_device, [x_voltage, y_voltage])


def _calculate_length(voltage: float, axis: str) -> float:
    """
    Переводит значения напряжения в длину с учётом знака.
    :param voltage: Значение напряжения
    :param axis: ось
    :return: расчётная длина
    """
    if 3.3 >= voltage >= 1.650:
        return 0 - length_to_voltage(voltage, axis)
    elif 0 <= voltage < 1.650:
        return 0 + length_to_voltage(voltage, axis)


def get_position(serial_device: Serial) -> [float, float]:
    """

    :param serial_device: зеркала
    :return: [float, float] текущая позиция зеркал в длинах
    """
    serial_device.write(f"GETVOLTAGEFF".encode())
    time.sleep(0.1)
    data = serial_device.readline()

    if len(data) > 5:
        x_str, y_str = data.decode().split('|')

        if len(x_str) == len(y_str) == 5 and 0 <= float(x_str) <= 3.3 and 0 <= float(y_str) <= 3.3:
            x, y = float(x_str), float(y_str)

            x_length = _calculate_length(x, 'x')
            y_length = _calculate_length(y, 'y')

            return [x_length, y_length]
        else:
            # TODO сюда логгер с инфо о проблеме
            pass
    else:
        # TODO сюда логгер с инфо о проблеме
        pass
