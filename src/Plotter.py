import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

class Plotter:
    def __init__(self, fontsize=16, fontpath="/mnt/c/Windows/Fonts/verdana.ttf"):
        """Initialize plotting environment (fonts, styles)."""
        self.font = fm.FontProperties(fname=fontpath, size=fontsize)

    # ---------------------------------------------------
    # 1D Line Plot
    # ---------------------------------------------------
    def plot1D(self, x, y,  xlabel="x", ylabel="y",
               filename=None, marker=True):
        """General-purpose 1D plot with ticks, markers, frame, Verdana."""

        x = np.asarray(x)
        y = np.asarray(y)

        plt.figure()

        # Main line
        plt.plot(x, y, color="black", linewidth=1.5)

        # Markers
        if marker:
            idx = np.linspace(0, len(x)-1, 20, dtype=int)
            plt.plot(x[idx], y[idx], "o", color="black", linestyle="none")

        # Labels + title
        plt.xlabel(xlabel, fontproperties=self.font)
        plt.ylabel(ylabel, fontproperties=self.font)

        ax = plt.gca()

        # Ticks
        ax.tick_params(which="major", direction="in", length=7, width=1.2,
                       top=True, bottom=True, left=True, right=True)
        ax.tick_params(which="minor", direction="in", length=4, width=0.8,
                       top=True, bottom=True, left=True, right=True)
        ax.minorticks_on()

        # Apply font to tick labels
        for lbl in ax.get_xticklabels() + ax.get_yticklabels():
            lbl.set_fontproperties(self.font)

        # Border
        for spine in ax.spines.values():
            spine.set_linewidth(1.0)
            spine.set_color("black")

        # No grid
        plt.grid(False)

        plt.subplots_adjust(left=0.15, bottom=0.15)

        # Save figure
        if filename:
            plt.savefig(filename, dpi=200)

        plt.close()

    def plot2x1(self, Data, Labels, filename=None, marker=True):
        """
        Create a 2x1 subplot figure.
        Data  = [x1, y1, x2, y2]
        Labels = ["xlabel1", "ylabel1", "xlabel2", "ylabel2"]
        """
    
        x1, y1, x2, y2 = map(np.asarray, Data)
        xlabel1, ylabel1, xlabel2, ylabel2 = Labels
    
        fig, axes = plt.subplots(2, 1, figsize=(6, 5))
    
        # -----------------------------
        # Helper for styling each plot
        # -----------------------------
        def style(ax, x, y, xlabel, ylabel):
            # Main line
            ax.plot(x, y, color="black", linewidth=1.5)
    
            # Markers
            if marker:
                idx = np.linspace(0, len(x)-1, 20, dtype=int)
                ax.plot(x[idx], y[idx], "o", color="black", linestyle="none")
    
            # Labels
            ax.set_xlabel(xlabel, fontproperties=self.font)
            ax.set_ylabel(ylabel, fontproperties=self.font)
    
            # Ticks
            ax.tick_params(which="major", direction="in", length=7, width=1.2,
                           top=True, bottom=True, left=True, right=True)
            ax.tick_params(which="minor", direction="in", length=4, width=0.8,
                           top=True, bottom=True, left=True, right=True)
            ax.minorticks_on()
    
            # Tick font
            for lbl in ax.get_xticklabels() + ax.get_yticklabels():
                lbl.set_fontproperties(self.font)
    
            # Border
            for spine in ax.spines.values():
                spine.set_linewidth(1.0)
                spine.set_color("black")
    
            ax.grid(False)
    
        # Apply style for each subplot
        style(axes[0], x1, y1, xlabel1, ylabel1)
        style(axes[1], x2, y2, xlabel2, ylabel2)
    
        plt.subplots_adjust(top=0.95, left=0.15, bottom=0.12, hspace=0.35)
    
        if filename:
            plt.savefig(filename, dpi=200)
    
        plt.close()

    def plot1x2(self, Data, Labels, filename=None, marker=True):
        """
        Create a 1x2 subplot figure (left–right).
        Data   = [x1, y1, x2, y2]
        Labels = ["xlabel1", "ylabel1", "xlabel2", "ylabel2"]
        """
    
        x1, y1, x2, y2 = map(np.asarray, Data)
        xlabel1, ylabel1, xlabel2, ylabel2 = Labels
    
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    
        # ------------------------------------
        # Helper function to apply your style
        # ------------------------------------
        def style(ax, x, y, xlabel, ylabel):
            # Main line
            ax.plot(x, y, color="black", linewidth=1.5)
    
            # Markers
            if marker:
                idx = np.linspace(0, len(x)-1, 20, dtype=int)
                ax.plot(x[idx], y[idx], "o", color="black", linestyle="none")
    
            # Labels
            ax.set_xlabel(xlabel, fontproperties=self.font)
            ax.set_ylabel(ylabel, fontproperties=self.font)
    
            # Ticks
            ax.tick_params(which="major", direction="in", length=7, width=1.2,
                           top=True, bottom=True, left=True, right=True)
            ax.tick_params(which="minor", direction="in", length=4, width=0.8,
                           top=True, bottom=True, left=True, right=True)
            ax.minorticks_on()
    
            # Tick fonts
            for lbl in ax.get_xticklabels() + ax.get_yticklabels():
                lbl.set_fontproperties(self.font)
    
            # Frame
            for spine in ax.spines.values():
                spine.set_linewidth(1.0)
                spine.set_color("black")
    
            ax.grid(False)
    
        # Apply style for both subplots
        style(axes[0], x1, y1, xlabel1, ylabel1)
        style(axes[1], x2, y2, xlabel2, ylabel2)
    
        plt.subplots_adjust(left=0.08, right=0.95, bottom=0.15, wspace=0.30)
    
        if filename:
            plt.savefig(filename, dpi=200)
    
        plt.close()
     
