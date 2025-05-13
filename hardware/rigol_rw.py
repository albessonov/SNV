import struct
import time

import numpy as np
from pyvisa import ResourceManager
from scapy.sendrecv import sniff


RES = "USB0::0x1AB1::0x099C::DSG3G264300050::INSTR"
def setup(gain: int, start_freq: float, stop_freq: float, step_freq: float, logger):
    """
    Настраивает генератор сигналов для частотной развертки

    Args:
        gain: усиление в диапазоне [-20, 20] дБм
        start_freq: начальная частота [Гц] (9 kHz - 13.6 GHz)
        stop_freq: конечная частота [Гц] (9 kHz - 13.6 GHz)
        step_freq: шаг частоты [Гц] (должен быть > 0)

    Raises:
        ValueError: при недопустимых параметрах
        RuntimeError: при ошибке связи с устройством
    """
    # Проверка входных параметров
    if not (-130 <= gain <= 27):
        logger.log("Усиление должно быть в диапазоне [-130, 27] дБм", "Error", "setup")

    if not (9e3 <= start_freq <= 13.6e9) or not (9e3 <= stop_freq <= 13.6e9):
        logger.log("Частота должна быть в диапазоне 9 kHz - 13.6 GHz", "Error", "setup")

    if start_freq >= stop_freq:
        logger.log("Начальная частота должна быть меньше конечной", "Error", "setup")

    if step_freq <= 0:
        logger.log("Шаг частоты должен быть положительным", "Error", "setup")

    # Расчет количества точек
    points_number = int(round((stop_freq - start_freq) / step_freq)) + 1
    if points_number > 65535:
        logger.log(f"Слишком много точек ({points_number}), максимум 10001", "Error", "setup")

    try:
        rm = ResourceManager()
        with rm.open_resource(RES) as dev:  # Используем контекстный менеджер
            # Настройка параметров развертки
            dev.write(f':SWE:RES')
            dev.write(f':LEV {gain}dBm')
            dev.write(':SOUR1:FUNC:MODE SWE')
            dev.write(":SWE:MODE CONT")
            dev.write(":SWE:STEP:SHAP RAMP")
            dev.write(":SWE:TYPE STEP")

            # Установка частотных параметров
            dev.write(f":SWE:STEP:POIN {points_number}")
            dev.write(f":SWE:STEP:STAR:FREQ {start_freq}")
            dev.write(f":SWE:STEP:STOP:FREQ {stop_freq}")

            # Настройка триггера
            dev.write("SWE:POIN:TRIG:TYPE EXT")

            # Включение выхода
            dev.write(":OUTP 1")

    except Exception as e:
        logger.log(f"Ошибка связи с устройством: {str(e)}", "Error", "setup")
