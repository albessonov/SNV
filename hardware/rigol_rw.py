import struct
import time

import numpy as np
from pyvisa import ResourceManager
from scapy.sendrecv import sniff


RES = "USB0::0x1AB1::0x099C::DSG3G264300050::INSTR"


def packet_callback(packet):
    if packet.haslayer("Raw"):
        print(len(packet["Raw"].load))
        payload = bytes(packet["Raw"].load)[28:]

        # Защита от неверного размера
        if len(payload) < 58:
            return

        try:

            # Распаковка данных
            package_id = struct.unpack('<H', payload[1:3])[0]
            byte6 = struct.unpack('<B', payload[5:6])[0]
            flag = (byte6 >> 7) & 1
            flag_valid = byte6 & 0x1

            flag_pos = (byte6 & 0x10) >> 4
            flag_neg = (byte6 & 0x8) >> 3

            cnt_photon_1 = struct.unpack('<H', payload[6:8])[0]
            cnt_photon_2 = struct.unpack('<H', payload[8:10])[0]

            tp1 = [int.from_bytes(payload[10 + 4 * i:14 + 4 * i], byteorder="little") for i in range(0, 5 + 1)]
            tp1_a = [np.round((tp1[i] & 0x1F) * 0.18, 1) for i in range(len(tp1))]  # ns
            tp1_b = [np.round((tp1[i] >> 7) * 5, 1) for i in range(len(tp1))]  # ns
            tp1_r = [(tp1_a[i] + tp1_b[i]) for i in range(len(tp1_a))]  # ns

            tp2 = [int.from_bytes(payload[34 + 4 * i:38 + 4 * i], byteorder="little") for i in range(0, 5 + 1)]
            tp2_a = [np.round((tp2[i] & 0x1F) * 0.18, 1) for i in range(len(tp2))]  # ns
            tp2_b = [np.round((tp2[i] >> 7) * 5, 1) for i in range(len(tp2))]  # ns
            tp2_r = [(tp2_a[i] + tp2_b[i]) for i in range(len(tp2_a))]  # ns

            #print(len(payload),payload[-4:-1])

            count_pos = int.from_bytes(payload[58:59], byteorder="little")

            count_neg = int.from_bytes(payload[60:61], byteorder="little")

            # Создаем словарь с результатами
            # FIXME Есть определённая избыточность в получаемых данных, стоит разделить на два метода: один чисто для счёта фотонов, другой для корелляции
            result = {
                "package_id": package_id,
                "flag": flag,
                "flag_valid": flag_valid,
                "flag_neg": flag_neg,
                "flag_pos": flag_pos,
                "cnt_photon_1": cnt_photon_1,
                "cnt_photon_2": cnt_photon_2,
                "tp1_r": np.array(list(set(tp1_r))),
                "tp2_r": np.array(list(set(tp2_r))),
                "count_neg": count_neg,
                "count_pos": count_pos

            }
            if flag_valid == 1:
                # Отправляем данные через сигнал
                if flag_neg == 1 or flag_pos == 1:
                    pass
                    #print(f"Count: {count_pos}")
        except Exception:
            pass


def setup(gain: int, start_freq: float, stop_freq: float, step_freq: float):
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
    if not (-20 <= gain <= 20):
        raise ValueError("Усиление должно быть в диапазоне [-20, 20] дБм")

    if not (9e3 <= start_freq <= 13.6e9) or not (9e3 <= stop_freq <= 13.6e9):
        raise ValueError("Частота должна быть в диапазоне 9 kHz - 13.6 GHz")

    if start_freq >= stop_freq:
        raise ValueError("Начальная частота должна быть меньше конечной")

    if step_freq <= 0:
        raise ValueError("Шаг частоты должен быть положительным")

    # Расчет количества точек
    points_number = int(round((stop_freq - start_freq) / step_freq)) + 1
    if points_number > 10001:
        raise ValueError(f"Слишком много точек ({points_number}), максимум 10001")

    try:
        rm = ResourceManager()
        with rm.open_resource(RES) as dev:  # Используем контекстный менеджер
            # Настройка параметров развертки
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
        raise RuntimeError(f"Ошибка связи с устройством: {str(e)}") from e
