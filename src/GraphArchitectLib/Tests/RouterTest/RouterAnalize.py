import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Задаем диапазоны значений
L_n = np.logspace(-1, 4, 30)  # от 10 до 10000
C_n = np.linspace(1, 3, 30)  # от 1 до 100
Q_n = 1.9  # фиксированное качество
t_sc = 1.0  # масштабный коэффициент
w_Q = 0.5   # вес качества
w_c = 0.25   # вес стоимости
w_l = 0.25   # вес длины

# Создаем сетку значений
L_grid, C_grid = np.meshgrid(L_n, C_n)

# Вычисляем R_n
R_n = (t_sc * (w_Q * Q_n - w_c * C_grid)) / (w_l * np.log(L_grid+2))

# Создаем 3D график
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# Построение поверхности
surf = ax.plot_surface(np.log10(L_grid), C_grid, R_n,
                      cmap='viridis',
                      edgecolor='none')

# Настройка осей
ax.set_xlabel('log10(L_n)')
ax.set_ylabel('C_n')
ax.set_zlabel('R_n')
ax.set_title(f'Quality Score (Q_n = {Q_n})')

# Добавляем цветовую шкалу
fig.colorbar(surf)

plt.show()