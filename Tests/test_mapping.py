import numpy as np
import struct
from scapy.sendrecv import sniff
from hardware.spincore import impulse_builder
from hardware.mirrors import*
import time
import matplotlib.pyplot as plt
import pcapy

from hardware.spincore import impulse_builder_Cold as impulse_builderc

from Tests.utils import to_dict


time_to_collect = 100
import logging

print(serial)
time_to_collect = 100
impulse_builder(
                1,
                [0],
                [1],
                [0],
                [time_to_collect],
                time_to_collect,
                int(1E6),
                int(1E6)
            )
ph_tmp = []
devs = pcapy.findalldevs()

print("Интерфейсы:")
for i, d in enumerate(devs):
    print(f"{i}: {d}")

iface = devs[6]

# Открыть интерфейс
cap = pcapy.open_live(iface, 106, 0, 0)
cap.setfilter("udp and src host 192.168.1.2")

prev = 0

# Обработка пакета
def handle_packet(hdr, packet):
    global prev
    rw = packet[42:]
    k = to_dict(rw)
    print(k)
    """if k['flag_neg'] == k['flag_pos'] == 1:
        print(k)"""

# Цикл захвата
cap.loop(3, handle_packet)  # 0 = бесконечно
    
