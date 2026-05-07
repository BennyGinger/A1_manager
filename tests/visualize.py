import numpy as np
import matplotlib.pyplot as plt


def generate_figure8_path(
    x0,
    y0,
    amplitude_x=3000,
    amplitude_y=3000,
    n_points=12,
    n_loops=1,
    vertical=False
):

    t = np.linspace(0, 2*np.pi*n_loops, n_points*n_loops)

    if not vertical:
        # Horizontal figure-8
        x = x0 + amplitude_x * np.sin(t)
        y = y0 + amplitude_y * np.sin(2*t)

    else:
        # Vertical figure-8
        x = x0 + amplitude_x * np.sin(2*t)
        y = y0 + amplitude_y * np.sin(t)

    return x, y


# Example center coordinate (A1 well)
x0 = 49205
y0 = -32139


# Generate paths
x_h, y_h = generate_figure8_path(
    x0, y0,
    amplitude_x=2000,
    amplitude_y=3000,
    vertical=False
)

x_v, y_v = generate_figure8_path(
    x0, y0,
    amplitude_x=3000,
    amplitude_y=3000,
    vertical=True
)


# Plot
plt.figure(figsize=(8,8))

plt.plot(x_h, y_h, '*-', label='Horizontal Figure-8')
plt.plot(x_v, y_v, '*-', label='Vertical Figure-8')

# Mark center point
plt.scatter(x0, y0, color='red', s=100, label='Well Center')

plt.xlabel('Stage X coordinate')
plt.ylabel('Stage Y coordinate')

plt.title('Microscope Stage Figure-8 Trajectories')

plt.axis('equal')   # Important: keeps geometry correct
plt.grid(True)
plt.legend()

plt.show()