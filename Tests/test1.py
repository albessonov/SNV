import pcapy

from hardware.spincore import impulse_builder_Cold as impulse_builderc

from Tests.utils import to_dict
time = 125330
impulse_builderc(
             1,
             [0],
             [1],
             [0],
             [time],
            time,
             int(1e0),
             int(1e0)
         )

# Выбрать вручную нужный интерфейс
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
    """if k['flag_neg'] == k['flag_pos'] == 1:
        print(k)"""
    print(f"id: {k['package_id']}   flagPar: {k['flag_parity']}     count: {k['count_hundred']}")


# Цикл захвата
cap.loop(0, handle_packet)  # 0 = бесконечно