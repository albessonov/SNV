import numpy as np
import struct
from scapy.sendrecv import sniff
from hardware.spincore import impulse_builder_Cold as impulse_builderc
import time
import matplotlib.pyplot as plt
import hardware.spincore as sp
from pyvisa import ResourceManager
import logging

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

# Настройки генератора
RES = "USB0::0x1AB1::0x099C::DSG3G264300050::INSTR"
freq = 2.80058582 * 1e9  # Гц
start = 10  # нс
stop = 1500  # нс
step = 50  # нс
gain = -15  # дБм
n_avg = 100000  # количество усреднений
t_count = 3000 # нс

filename = ""

# Инициализация генератора
rm = ResourceManager()
dev = rm.open_resource(RES)
dev.write(f':LEV {gain}dBm')
dev.write(f':FREQ {freq}')
dev.write(":OUTP 1")
dev.write(":MOD:STAT 1")
dev.write(":PULM:SOUR EXT")
dev.write(":PULM:STAT 1")

# Массивы для данных
Times = np.arange(start=start, stop=(stop + step), step=step)
ph_raw = np.zeros(len(Times))  # Сигнал под СВЧ
norm_raw = np.zeros(len(Times))  # Опорный сигнал (без СВЧ)

# Функция обработки пакетов
ph_tmp = []
def packet_callback(packet):
    global ph_tmp
    if packet.haslayer("Raw"):
        payload = bytes(packet["Raw"].load)[42:]
        if len(payload) < 58:
            return
        try:
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

            if flag_valid == 1 and flag_pos == 1:
                ph_tmp.append(result["count_pos"])
        except Exception as e:
            pass

# Основной цикл измерений
#

#     print(f"Усреднение {n + 1}/{n_avg}")
#
#     # 1. Измерение нормировки (без СВЧ)
#     for j, t in enumerate(Times):
#         impulse_builderc(
#             2,
#             [0, 2],
#             [1, 1],
#             [0, 0],
#             [500, 500],
#             2,
#             int(1),
#             int(1e6)
#         )
#         sp.startPb()
#         while True:
#             sniff(iface="Ethernet", filter="src host 192.168.1.2",
#                   prn=packet_callback, timeout=0.800, store=False)
#             if len(ph_tmp) > 3:
#                 break
#             ph_tmp = []
#         norm_raw[j] += sum(ph_tmp[:2])
#         ph_tmp = []
#     sp.stopPb()
# 1. Норма без СВЧ
impulse_builderc(
             2,
             [0, 2],
             [1, 1],
             [0, 0],
             [t_count, t_count],
            2,
             int(1),
             int(1e6)
         )

"""norm_raw_s = 0
sp.startPb()
for i in range(3):
    while True:
        sniff(iface="Ethernet", filter="src host 192.168.1.2",
             prn=packet_callback, timeout=0.800, store=False)
        if len(ph_tmp) > 3:
            break
        ph_tmp = []
    norm_raw_s += sum(ph_tmp[:2])
    ph_tmp = []
sp.stopPb()
print(norm_raw_s)
norm_raw_s /= 3"""

    # 2. Измерение сигнала (под СВЧ)
for n in range(n_avg):
    print(f"Усреднение {n + 1}/{n_avg}")
    for c, t in enumerate(Times):
        impulse_builderc(
                3,
                [0, 1, 2],
                [1, 1, 1],
                [t+62, 0,t + 62],
                [t + 62 + t_count, t, t + 62 + t_count],
                2,
                int(1),
                int(1e6)
            )
        sp.startPb()
        while True:
            sniff(iface="Ethernet", filter="src host 192.168.1.2",
                      prn=packet_callback, timeout=0.800, store=False)
            if len(ph_tmp) > 3:
                break
            ph_tmp = []
        ph_raw[c] += sum(ph_tmp[:2])

        with open(f'data/{int(start)}_{int(stop)}_{int(step)}_{int(n_avg)}_{filename}.csv', 'w') as file:
            file.writelines(f"{ph_raw[i + 1]}\n" for i in range(len(ph_raw) - 1))

        ph_tmp = []
        sp.stopPb()
       # print(ph_raw)

# Усреднение данных
#norm_avg = norm_raw / n_avg
#ph_avg = ph_raw / n_avg
ph_avg = ph_raw

"""# Нормировка с защитой от деления на ноль
ph_norm = np.zeros_like(ph_avg)
for i in range(len(ph_avg)):
    if norm_raw_s != 0:
        ph_norm[i] = ph_avg[i] / norm_raw_s
    else:
        ph_norm[i] = ph_avg[i]  # или ph_avg[i], если нормировка не критична"""

with open(f'data/{int(start)}_{int(stop)}_{int(step)}_{int(n_avg)}_{filename}.csv', 'w') as file:
    file.writelines(f"{ph_raw[i + 1]}\n" for i in range(len(ph_raw) - 1))

# Выключение генератора
dev.write(":OUTP 0")
dev.write(":MOD:STAT 0")
dev.write(":PULM:STAT 0")
dev.close()

# Построение графика
plt.figure(figsize=(10, 6))
plt.plot(Times[1:], ph_norm[1:], 'o-', label='Нормированный сигнал')
plt.xlabel('Время (нс)', fontsize=12)
plt.ylabel('Нормированная амплитуда', fontsize=12)
plt.title('Зависимость сигнала от времени', fontsize=14)
plt.grid(True)
plt.show()