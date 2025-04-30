import struct
import time

import numpy as np
from pyvisa import ResourceManager
from scapy.sendrecv import sniff

from hardware.spincore import impulse_builder

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
    Args:
        gain: усиление, [дБм]
        start_freq: начальная частота, [Гц]
        stop_freq: конечная частота, [Гц]
        step_freq: шаг частоты, [Гц]
    """
    if 9 * 1E3 <= start_freq <= 13.6 * 1E9 and 9 * 1E3 <= stop_freq <= 13.6 * 1E9:
        rm = ResourceManager()
        dev = rm.open_resource(RES)

        points_number = np.round((stop_freq - start_freq) / step_freq, 0) + 1


        dev.write(f':LEV {gain}dBm')

        dev.write(':SOUR1:FUNC:MODE SWE')
        dev.write(":SWE:MODE CONT")
        dev.write(":SWE:STEP:SHAP RAMP")
        dev.write(":SWE:TYPE STEP")

        dev.write(f":SWE:STEP:POIN {points_number}")
        dev.write(f":SWE:STEP:STAR:FREQ {start_freq}")
        dev.write(f":SWE:STEP:STOP:FREQ {stop_freq}")

        dev.write("SWE:POIN:TRIG:TYPE EXT")

        dev.write(":OUTP 1")

        dev.close()
    else:
        raise ValueError("Превышен диапазон")


setup(-20, 2.83 * 1E9, 2.9 * 1E9, 500*1E3)
# Триггер
input("enter")
print("Поехали !")
impulse_builder(2, [0, 1], [1, 1], [0, 10], [10, 20], 10, 1000000, 1)
sniff(iface="Ethernet", filter="src host 192.168.1.2", prn=packet_callback, count=0)
