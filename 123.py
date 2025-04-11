"""from socket import *
server = socket(AF_INET, SOCK_DGRAM)
#IP-v4 169.254.120.95
server.bind(('169.254.120.95', 5353))
data, client_address = server.recvfrom(2**9)
print(f"Получены данные от {client_address}: {data.decode()}")"""
# Global variable to signal when to stop sniffing and return data
import struct
from scapy.all import sniff

# Глобальные переменные
data_ready = False
data = []
init = False  # Инициализация глобальной переменной `init`

def packet_callback(packet):
    global init  # Объявляем переменную `init` как глобальную
    global data
    global data_ready

    if packet.haslayer("IP") and packet.haslayer("UDP"):
        payload = bytes(packet["UDP"].payload)

        # Распаковка данных
        package_id = struct.unpack('<H', payload[1:3])[0]
        byte6 = struct.unpack('<B', payload[5:6])[0]
        flag = (byte6 >> 7) & 1
        cnt_photon_1 = struct.unpack('<H', payload[6:8])[0]
        cnt_photon_2 = struct.unpack('<H', payload[8:10])[0]
        tp1 = [struct.unpack('<I', payload[10+4*i:14+4*i])[0] for i in range(0, 5 + 1)]
        tp1_1 = [(tp1[i] & 0b111111) * 5 for i in range(len(tp1))]  # ns
        tp1_2 = [((tp1[i] >> 7) & ((1 << 25) - 1)) * 185 * 1E-3 for i in range(len(tp1))]  # ns
        tp1_r = [round((tp1_1[i] + tp1_2[i]), 3) for i in range(len(tp1_1))]  # ns

        tp2 = [struct.unpack('<I', payload[34+4*i:38+4*i])[0] for i in range(0, 5 + 1)]
        tp2_1 = [(tp2[i] & 0b111111) * 5 for i in range(len(tp2))]  # ns
        tp2_2 = [((tp2[i] >> 7) & ((1 << 25) - 1)) * 185 * 1E-3 for i in range(len(tp2))]  # ns
        tp2_r = [round((tp2_1[i] + tp2_2[i]), 3) for i in range(len(tp2_1))]  # ns

        # Создаем словарь с результатами
        result = {
            "package_id": package_id,
            "flag": flag,
            "cnt_photon_1": cnt_photon_1,
            "cnt_photon_2": cnt_photon_2,
            "tp1_r": tp1_r,
            "tp2_r": tp2_r,
        }

        if flag and not init:
            init = True
            data.append(result)
        elif not flag and init:
            data.append(result)
        elif flag and init:
            # Возвращаем данные, когда flag и init == True
            data_ready = True
            return  # Завершаем callback, что прерывает дальнейшее выполнение sniffer

# Функция для начала захвата пакетов
def start_sniffing():
    global data_ready
    global data
    global init

    # Запуск захвата пакетов, пока не будет установлен флаг data_ready
    sniff(iface="Ethernet", filter="udp and src host 192.168.1.2", prn=packet_callback, stop_filter=lambda x: data_ready)

    return data

# Основной запуск
result_data = start_sniffing()
a = result_data[0]['tp1_r']
b = result_data[0]['tp2_r']
print(a,b)
d = [[a[j] - b[i] for i in range(len(b))] for j in range(len(a))]
k = [item for sublist in d for item in sublist]
print(k)
