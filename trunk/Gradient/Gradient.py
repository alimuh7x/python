#!/home/alimuh7x/myenv/bin/python3
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# Add src/ folder to Python's module search path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(CURRENT_DIR, "..", "src")
sys.path.append(os.path.realpath(SRC_PATH))

OUTPUT_DIR = Path(__file__).parent


def main() -> None:
    font = fm.FontProperties(fname="/mnt/c/Windows/Fonts/verdana.ttf", size=12)

    # ========== Gradient Plot ==========
    x, y = np.meshgrid(np.arange(-5, 5.5, 0.5), np.arange(-5, 5.5, 0.5))
    T = np.exp(-0.1 * (x**2 + y**2))

    # Compute gradients
    Tx, Ty = np.gradient(T, 0.5, 0.5)

    fig, ax = plt.subplots(figsize=(8, 7))
    contour = ax.contourf(x, y, T, 20, cmap='jet')
    plt.colorbar(contour, ax=ax)
    ax.quiver(x, y, Tx, Ty, color='k')
    ax.set_title('2D Gradient Field', fontproperties=font)
    ax.set_xlabel('x', fontproperties=font)
    ax.set_ylabel('y', fontproperties=font)
    ax.set_aspect('equal')
    ax.axis('tight')

    filename = OUTPUT_DIR / "gradient_plot.png"
    plt.savefig(filename, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved: gradient_plot.png")

    # ========== 3D Surface Plot ==========
    x, y = np.meshgrid(np.arange(-10, 10.1, 0.1), np.arange(-10, 10.1, 0.1))
    r = np.sqrt(x**2 + y**2)
    z = np.sin(r) / (r + np.finfo(float).eps)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(x, y, z, cmap='viridis', edgecolor='none', antialiased=True)
    ax.set_title('Smooth 3D Surface Plot', fontproperties=font)
    ax.set_xlabel('x', fontproperties=font)
    ax.set_ylabel('y', fontproperties=font)
    ax.set_zlabel('z', fontproperties=font)
    fig.colorbar(surf, ax=ax, shrink=0.5)

    filename = OUTPUT_DIR / "Surf.png"
    plt.savefig(filename, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved: Surf.png")


if __name__ == "__main__":
    main()
