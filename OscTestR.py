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

RES = "USB0::0x1AB1::0x099C::DSG3G264300050::INSTR"

freq = 2.850*1E9 #MHz
start = 10 #ns 
stop = 1E3 #ns
step = 10 #ns
gain = -20
# Количество усреднений
n_avg = 10
assert n_avg > 0

rm = ResourceManager()
dev = rm.open_resource(RES)
dev.write(f':LEV {gain}dBm')
dev.write(f':FREQ {freq}')

dev.write(":OUTP 1")
dev.write(":MOD:STAT 1")
dev.write(":PULM:SOUR EXT")
dev.write(":PULM:STAT 1")

Times = np.arange(start=start, stop=(stop+step), step=step)
ph = np.zeros(len(Times))

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
                #print(result)
                ph_tmp.append(result["count_pos"])
        except Exception as e:
            pass

c = 0

for n in range(n_avg+1):
    for t in Times: 
        time.sleep(0.002)
        impulse_builderc(
             3,
             [0,1,2],
             [1,1,1],
             [62,0,62],
             [t+62,t,t+62],
             2,
             int(1),
             int(1E6)
             )
        sp.startPb
        while 1:
            sniff(iface="Ethernet", filter="src host 192.168.1.2", prn=packet_callback, timeout=0.800, store=False)
            if len(ph_tmp) > 3:
                break
            else:
                ph_tmp = []
        #h[c] += round(sum(ph_tmp[:2])/3)
        ph[c] += round(sum(ph_tmp[:2])) 
        ph_tmp = []
        c += 1
    c = 0
    sp.stopPb
    print("Текущее усреднение:", n)
    if n == n_avg:
         ph = [ph[i]/n_avg for i in range(len(ph))]
sp.closePb

dev.write(":OUTP 0")
dev.write(":MOD:STAT 0")
dev.write(":PULM:STAT 0")
dev.close()

plt.plot(Times[1:], ph[1:])
plt.show()

