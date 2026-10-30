"""Matplotlib dark documentary theme using the Barlow fonts."""
import glob
import os

from matplotlib import font_manager, rcParams

from common_paths import FONTS

_done = False


def apply():
    global _done
    if _done:
        return
    for f in glob.glob(os.path.join(FONTS, "*.ttf")):
        font_manager.fontManager.addfont(f)
    rcParams.update({
        "font.family": "Barlow",
        "font.size": 22,
        "axes.facecolor": "#05080f",
        "figure.facecolor": "#05080f",
        "axes.edgecolor": "#3a4456",
        "axes.labelcolor": "#aab4c6",
        "xtick.color": "#8c98ac",
        "ytick.color": "#8c98ac",
        "text.color": "#ecf0f7",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#1c2433",
        "grid.linewidth": 1.0,
        "xtick.labelsize": 22,
        "ytick.labelsize": 22,
        "axes.labelsize": 24,
        "lines.antialiased": True,
        "lines.solid_capstyle": "round",
        "axes.axisbelow": True,
        "mathtext.fontset": "custom",
        "mathtext.rm": "Barlow",
        "mathtext.it": "Barlow:italic",
        "mathtext.bf": "Barlow:bold",
    })
    _done = True
