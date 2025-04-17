import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate

# Параметры (в наносекундах)
tau_max_ns = 100*1e6  # 1 мс = 1,000,000 нс
#bin_width_ns = 0.185  # 185 пс = 0.185 нс
bin_width_ns = 10  # 10 нс
num_bins = int(np.round(tau_max_ns / bin_width_ns))  # Целое число бинов

# Фиксированные бины через linspace (для точного контроля)
bins = np.linspace(0, tau_max_ns, num_bins + 1)

# Пример данных (временные метки в наносекундах)
all_t1 = [
    np.array([10, 20,30, 40, 50, 60])
]

all_t2 = [
    np.array([120, 301, 304, 200, 1001, 10*1e6])
]

# Проверка, что метки не превышают tau_max_ns
all_t1 = [t[(t >= 0) & (t <= tau_max_ns)] for t in all_t1]
all_t2 = [t[(t >= 0) & (t <= tau_max_ns)] for t in all_t2]

# Инициализация массива корреляции
cross_corr = np.zeros(2 * num_bins - 1)

for t1, t2 in zip(all_t1, all_t2):
    binary1, _ = np.histogram(t1, bins=bins)
    binary2, _ = np.histogram(t2, bins=bins)

    corr = correlate(binary1, binary2, mode='full')
    cross_corr += corr  # Теперь размеры совпадают!

# Нормализация
avg_n1 = np.mean([len(t) for t in all_t1])
avg_n2 = np.mean([len(t) for t in all_t2])
norm_factor = len(all_t1) * avg_n1 * avg_n2 * bin_width_ns
g2 = cross_corr / norm_factor

# Лаги (в наносекундах)
lags = (np.arange(len(cross_corr)) - (num_bins - 1)) * bin_width_ns

# График
plt.plot(lags, g2)
plt.xlabel('Задержка τ, нс')
plt.ylabel('g²(τ)')
plt.title('Взаимная корреляционная функция')
plt.grid(True)
plt.xlim(-tau_max_ns*1.05, tau_max_ns*1.05)
plt.ylim(ymin=0)
plt.show()