from __future__ import annotations

from pathlib import Path

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.font_manager as fm

_FONT_PATH = Path("/mnt/c/Windows/Fonts/verdana.ttf")
_FONT_SIZE = 16


def _load_font(font_path: Path, size: int) -> fm.FontProperties:
    try:
        return fm.FontProperties(fname=str(font_path), size=size)
    except OSError:
        return fm.FontProperties(size=size)


_FONT_PROPERTIES = _load_font(_FONT_PATH, _FONT_SIZE)


def _apply_plotter_axis_style(ax: Axes) -> None:
    ax.tick_params(
        which    =  "major",
        direction=  "in",
        length   =  7,
        width    =  1.2,
        top      =  True,
        bottom   =  True,
        left     =  True,
        right    =  True,
    )
    ax.tick_params(
        which       = "minor",
        direction   = "in",
        length      = 4,
        width       = 0.8,
        top         = True,
        bottom      = True,
        left        = True,
        right       = True,
    )
    ax.minorticks_on()

    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontproperties(_FONT_PROPERTIES)

    for spine in ax.spines.values():
        spine.set_linewidth(1.0)
        spine.set_color("black")


def _ensure_parent(path: Path) -> None:
    """Ensure that the parent directory exists for `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)


def _decorate_axis(
    ax: Axes,
    x_label: str,
    y_label: str,
    title: str | None = None,
    logx: bool = False,
    logy: bool = False,
    grid: bool = False,
) -> None:
    """Apply consistent labels, scales, and grid lines to an axis."""
    ax.set_xlabel(x_label, fontproperties=_FONT_PROPERTIES)
    ax.set_ylabel(y_label, fontproperties=_FONT_PROPERTIES)

    if title:
        ax.set_title(title, fontproperties=_FONT_PROPERTIES)

    if logx:
        ax.set_xscale("log")

    if logy:
        ax.set_yscale("log")

    _apply_plotter_axis_style(ax)
    ax.grid(grid)



def _plot_markers_if_requested(
    ax: Axes,
    x: np.ndarray,
    y: np.ndarray,
    marker: bool,
    sample_points: int = 20,
) -> None:
    """Add Plotter-style markers when requested."""
    if not marker:
        return

    x_arr = np.asarray(x)
    y_arr = np.asarray(y)

    if x_arr.size == 0:
        return

    num_markers = min(x_arr.size, sample_points)
    if num_markers <= 0:
        return

    indices = np.linspace(0, x_arr.size - 1, num_markers, dtype=int)
    ax.plot(x_arr[indices], y_arr[indices], "o", color="black", linestyle="none")


def save_dual_plot(
    x: np.ndarray,
    y1: np.ndarray,
    y2: np.ndarray,
    x_label: str,
    y_label: str,
    y1_label: str,
    y2_label: str,
    filename: Path | str,
    title: str | None = None,
    logx: bool = False,
    logy: bool = False,
    *,
    marker: bool = False,
    grid: bool = False,
) -> None:
    """Render two data series on the same axes and write the figure to disk.

    Grid lines are disabled by default and markers stay off unless requested.
    """
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(x, y1, label=y1_label, linewidth=2)
    _plot_markers_if_requested(ax, x, y1, marker)
    ax.plot(x, y2, label=y2_label, linewidth=2)
    _plot_markers_if_requested(ax, x, y2, marker)
    _decorate_axis(
        ax,
        x_label,
        y_label,
        title=title,
        logx=logx,
        logy=logy,
        grid=grid,
    )
    ax.legend(prop=_FONT_PROPERTIES)
    _save_figure(fig, filename)



def save_single_plot(
    x: np.ndarray,
    y: np.ndarray,
    x_label: str,
    y_label: str,
    filename: Path | str,
    title: str | None = None,
    logx: bool = False,
    logy: bool = False,
    *,
    marker: bool = False,
    grid: bool = False,
) -> None:
    """Render a single line plot and write the figure to disk.

    Markers and grid lines stay off unless requested by keywords.
    """
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(x, y, linewidth=2)
    _plot_markers_if_requested(ax, x, y, marker)
    _decorate_axis(
        ax,
        x_label,
        y_label,
        title=title,
        logx=logx,
        logy=logy,
        grid=grid,
    )
    _save_figure(fig, filename)


def save_four_subplot(
    data: np.ndarray,
    column_labels: list[str],
    filename: Path | str,
    rows: int = 2,
    cols: int = 2,
    sharex: bool = True,
    *,
    marker: bool = False,
    grid: bool = False,
) -> None:
    """Create up to four subplots sharing the first column as the x-axis.

    Marker symbols and grid visibility are disabled by default.
    """
    fig, axes = plt.subplots(rows, cols, figsize=(12, 9), sharex=sharex)
    axes_list = axes.flatten()
    x = data[:, 0]

    for idx, ax in enumerate(axes_list, start=1):
        if idx >= data.shape[1]:
            ax.remove()
            continue

        ax.plot(x, data[:, idx], linewidth=1.5)
        _plot_markers_if_requested(ax, x, data[:, idx], marker)
        _decorate_axis(
            ax,
            column_labels[0],
            column_labels[idx],
            title=column_labels[idx],
            grid=grid,
        )

    fig.tight_layout()
    _save_figure(fig, filename)


def _save_figure(fig: Figure, filename: Path | str) -> None:
    """Persist a figure to disk using the Agg backend."""
    path = Path(filename)
    _ensure_parent(path)
    fig.savefig(path, dpi=300)
    plt.close(fig)
