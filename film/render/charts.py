"""Animated data charts (matplotlib), all driven directly by the public datasets."""
import numpy as np
from matplotlib.patches import Rectangle

from render import data
from render.base import (AMBER, BG, BLUE, CO2, CYAN, DIM, INK, MUTED, RED, TEAL, VIOLET, MplScene, draw_text, ease,
                         ease_io, ease_out, font, hexc, lerp, ramp, source_tag)

A = hexc(CO2)
C = hexc(CYAN)
M = hexc(MUTED)


def _title(fig, title, sub=None, x=0.057, y=0.905):
    fig.text(x, y, title, fontsize=40, fontweight="light", color=hexc(INK), va="bottom")
    if sub:
        fig.text(x, y - 0.012, sub, fontsize=24, color=M, va="top")


class Keeling(MplScene):
    def setup(self):
        p = self.p
        m = data.mlo_monthly()
        self.x, self.y = m.dec.values, m.avg.values
        self.ax = self.fig.add_axes([0.075, 0.13, 0.86, 0.68])
        ax = self.ax
        ax.set_ylabel("CO$_2$ (ppm)")
        self.glow, = ax.plot([], [], color=A, lw=9, alpha=0.18)
        self.line, = ax.plot([], [], color=A, lw=2.6)
        self.head, = ax.plot([], [], "o", color="white", ms=9, mec=A, mew=3)
        self.lab = ax.text(0, 0, "", fontsize=26, color="white", fontweight="medium", va="bottom")
        if p.get("glob"):
            g = data.global_monthly()
            self.gx, self.gy = g.dec.values, g.avg.values
            self.gline, = ax.plot([], [], color=C, lw=2.0, alpha=0.95)
            self.fig.text(0.62, 0.84, "— Mauna Loa", color=A, fontsize=24)
            self.fig.text(0.76, 0.84, "— Global surface mean (NOAA)", color=C, fontsize=24)
        if p.get("preind"):
            ax.axhline(280, color=hexc(MUTED), lw=1.6, ls=(0, (6, 6)))
            ax.text(p["t0"] + 1, 283, "Pre-industrial level ≈ 280 ppm (ice cores)", color=M, fontsize=22, va="bottom")
        _title(self.fig, "Carbon dioxide at Mauna Loa, Hawaiʻi", "Monthly mean, parts per million")
        self.fig.text(0.057, 0.035, "Data: NOAA Global Monitoring Laboratory & Scripps Institution of Oceanography",
                      color=M, fontsize=19)

    def draw(self, t):
        p = self.p
        t0, t1 = p["t0"], p["t1"]
        ylim = p["ylim"]
        mode = p.get("mode", "draw")
        if mode == "draw":
            k = ease_io(min(t / (0.8 * self.dur), 1))
            head = lerp(p.get("from", t0 + 0.4), t1, k)
        else:
            head = t1
        sel = (self.x <= head) & (self.x >= t0 - 1)
        xs, ys = self.x[sel], self.y[sel]
        self.line.set_data(xs, ys)
        self.glow.set_data(xs, ys)
        ax = self.ax
        ax.set_xlim(t0 - 0.3, t1 + (t1 - t0) * 0.04)
        ax.set_ylim(*ylim)
        if p.get("glob"):
            gs = self.gx <= head
            self.gline.set_data(self.gx[gs], self.gy[gs])
        if len(xs):
            self.head.set_data([xs[-1]], [ys[-1]])
            yr, mo = int(xs[-1]), int(round((xs[-1] - int(xs[-1])) * 12 + 0.5))
            mon = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][min(max(mo, 1), 12) - 1]
            self.lab.set_position((xs[-1] - (t1 - t0) * 0.012, ys[-1] + (ylim[1] - ylim[0]) * 0.025))
            self.lab.set_text(f"{mon} {yr}  ·  {ys[-1]:.1f} ppm")
            self.lab.set_ha("right")
        if p.get("callout") == "latest":
            i = int(np.argmax(self.y))
            a = ramp(t, 1.5, 1.5)
            if not hasattr(self, "co"):
                self.co = ax.annotate(f"May 2026: {self.y[i]:.2f} ppm\nhighest monthly mean on record",
                                      xy=(self.x[i], self.y[i]), xytext=(self.x[i] - 30, self.y[i] + 2),
                                      color="white", fontsize=28, ha="left", va="center",
                                      arrowprops=dict(arrowstyle="-", color="white", lw=1.5))
                self.lab.set_visible(False)
            self.co.set_alpha(a)
            self.co.arrow_patch.set_alpha(a)


class Seasonal(MplScene):
    PERIODS = [(1959, 1968, "#4f7fd6"), (1979, 1988, "#6fb3c9"), (1999, 2008, "#e6b35a"), (2016, 2025, A)]

    def setup(self):
        m = data.mlo_monthly()
        m = m.assign(res=m.avg - m.deseas)
        self.curves = []
        for y0, y1, c in self.PERIODS:
            s = m[(m.year >= y0) & (m.year <= y1)].groupby("month").res.mean()
            self.curves.append((np.arange(1, 13), s.reindex(range(1, 13)).values, c, f"{y0}–{y1}"))
        self.ax = self.fig.add_axes([0.08, 0.14, 0.62, 0.66])
        ax = self.ax
        ax.set_xlim(0.7, 12.3)
        ax.set_ylim(-4.2, 4.2)
        ax.set_xticks(range(1, 13), ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"])
        ax.axhline(0, color=hexc(DIM), lw=1.2)
        ax.set_ylabel("ppm above / below trend")
        self.lines = [ax.plot([], [], color=c, lw=4)[0] for _, _, c, _ in self.curves]
        self.labels = [self.fig.text(0.74, 0.70 - 0.075 * i, f"—  {lab}", color=c, fontsize=30, alpha=0)
                       for i, (_, _, c, lab) in enumerate(self.curves)]
        _title(self.fig, "The yearly breath", "Mauna Loa CO$_2$ with the long-term rise removed, averaged by month")
        self.fig.text(0.74, 0.25, "Peak: May\nLow: September–October", color=hexc(INK), fontsize=28, linespacing=1.5)
        self.fig.text(0.057, 0.035, "Data: NOAA GML / Scripps — monthly mean minus de-seasonalized trend", color=M, fontsize=19)

    def draw(self, t):
        n = len(self.curves)
        for i, (x, y, c, lab) in enumerate(self.curves):
            k = ramp(t, 0.5 + i * self.dur * 0.16, self.dur * 0.18)
            npts = 1 + k * 11
            j = int(np.floor(npts))
            xs, ys = list(x[:j]), list(y[:j])
            if j < 12 and k > 0:
                f = npts - j
                xs.append(x[j - 1] + f)
                ys.append(y[j - 1] + (y[j] - y[j - 1]) * f)
            self.lines[i].set_data(xs, ys)
            self.labels[i].set_alpha(min(k * 3, 1))


class Amplitude(MplScene):
    def setup(self):
        m = data.mlo_monthly()
        m = m.assign(res=m.avg - m.deseas)
        g = m.groupby("year").res.agg(["max", "min", "count"])
        g = g[(g["count"] >= 11) & (g.index >= 1959) & (g.index <= 2025)]
        self.yr, self.amp = g.index.values, (g["max"] - g["min"]).values
        self.smooth = np.convolve(self.amp, np.ones(9) / 9, mode="same")
        self.smooth[:4] = np.nan
        self.smooth[-4:] = np.nan
        self.ax = self.fig.add_axes([0.08, 0.14, 0.86, 0.66])
        ax = self.ax
        ax.set_xlim(1957, 2027)
        ax.set_ylim(4.5, 8.2)
        ax.set_ylabel("Seasonal swing (ppm)")
        self.sc = ax.scatter([], [], s=60, color=hexc(MUTED), alpha=0.8)
        self.ln, = ax.plot([], [], color=A, lw=5)
        _title(self.fig, "A deepening breath", "Peak-to-trough seasonal swing at Mauna Loa each year, with 9-year average")
        self.fig.text(0.057, 0.035, "Data: NOAA GML / Scripps. Arctic stations (e.g. Utqiaġvik, Alaska) show swings several times larger.", color=M, fontsize=19)

    def draw(self, t):
        k = ease_io(min(t / (0.7 * self.dur), 1))
        n = int(1 + k * (len(self.yr) - 1))
        self.sc.set_offsets(np.c_[self.yr[:n], self.amp[:n]])
        self.ln.set_data(self.yr[:n], self.smooth[:n])


class GrowthBars(MplScene):
    def setup(self):
        a = data.mlo_annual()
        a = a[a.year >= 1960]
        self.yr, self.inc = a.year.values, a.inc.values
        hl = set(self.p.get("highlight", []))
        self.ax = self.fig.add_axes([0.07, 0.14, 0.88, 0.66])
        ax = self.ax
        self.bars = ax.bar(self.yr, np.zeros_like(self.inc), width=0.78,
                           color=[A if y in hl else "#6d7f9e" for y in self.yr])
        ax.set_ylim(0, 4.0)
        ax.set_ylabel("Increase over previous year (ppm)")
        self.hl = hl
        self.txt = {}
        for y, v in zip(self.yr, self.inc):
            if y in hl:
                self.txt[y] = ax.text(y, v + 0.08, f"{y}\n+{v:.2f}", ha="center", va="bottom", fontsize=22, color="white", alpha=0)
        self.dec_txt = []
        if not hl:
            for d0, d1 in [(1960, 1969), (1980, 1989), (2000, 2009), (2015, 2024)]:
                s = self.inc[(self.yr >= d0) & (self.yr <= d1)].mean()
                tx = ax.text((d0 + d1) / 2, s + 0.55, f"{d0}s avg\n{s:.2f}/yr" if d0 != 2015 else f"2015–24 avg\n{s:.2f}/yr",
                             ha="center", fontsize=22, color=hexc(INK), alpha=0)
                self.dec_txt.append((d0, tx))
        _title(self.fig, "How fast is it rising?", "Annual increase in the yearly mean CO$_2$ at Mauna Loa")
        self.fig.text(0.057, 0.035, "Data: NOAA GML / Scripps annual means. Highlighted: years following strong El Niño events.", color=M, fontsize=19)

    def draw(self, t):
        f = self.p.get("focus")
        ax = self.ax
        if f:
            k = ease_io(min(t / 3.0, 1))
            ax.set_xlim(lerp(1958.5, f[0] - 0.6, k), lerp(2026.5, f[1] + 0.6, k))
            grow = 1.0
        else:
            ax.set_xlim(1958.5, 2026.5)
            grow = None
        span = 0.75 * self.dur if not self.hl else 0.4 * self.dur
        for i, (b, y, v) in enumerate(zip(self.bars, self.yr, self.inc)):
            if grow is None:
                k = ease_out((t - span * i / len(self.yr)) / 0.8)
            else:
                k = 1.0
            b.set_height(v * max(k, 0))
        for y, tx in self.txt.items():
            tx.set_alpha(ramp(t, span + 0.5, 0.8) if not f else 1.0)
        for d0, tx in self.dec_txt:
            tx.set_alpha(ramp(t, span * (d0 - 1960 + 10) / 66 + 0.3, 0.8))


class EmissionsArea(MplScene):
    KEYS = [("coal_co2", "Coal", "#8d8a86"), ("oil_co2", "Oil", "#d9894a"), ("gas_co2", "Gas", "#5aa9e6"),
            ("cement_co2", "Cement", "#c9c37a"), ("flaring_co2", "Flaring", "#e05a47"), ("other_industry_co2", "Other", "#9a7fd1")]

    def setup(self):
        w = data.owid_world()
        w = w.loc[1750:2024]
        self.yr = w.index.values
        self.vals = np.vstack([w[k].fillna(0).values / 1000 for k, _, _ in self.KEYS])
        self.ax = self.fig.add_axes([0.07, 0.14, 0.78, 0.66])
        ax = self.ax
        ax.set_xlim(1750, 2026)
        ax.set_ylim(0, 42)
        ax.set_ylabel("Billion tonnes CO$_2$ per year")
        self.coll = None
        self.lbl = [self.fig.text(0.865, 0.20 + 0.0, "", fontsize=26, color=c) for _, _, c in self.KEYS]
        self.total = self.fig.text(0.865, 0.78, "", fontsize=46, color="white", fontweight="light")
        self.totl = self.fig.text(0.865, 0.745, "", fontsize=22, color=M)
        _title(self.fig, "Humanity's carbon dioxide, year by year", "Fossil fuels and industry, by source")
        self.fig.text(0.057, 0.035, "Data: Global Carbon Budget via Our World in Data (owid/co2-data)", color=M, fontsize=19)

    def draw(self, t):
        full = self.p.get("mode") == "full"
        head = 2024 if full else lerp(1750, 2024, ease_io(min(t / (0.85 * self.dur), 1)) ** 1.0)
        sel = self.yr <= head
        if self.coll:
            self.coll.remove()
        cols = [c for _, _, c in self.KEYS]
        self.coll = self.ax.stackplot(self.yr[sel], self.vals[:, sel], colors=cols, alpha=0.92, lw=0)
        self.coll = _Group(self.coll)
        n = sel.sum()
        cum = np.cumsum(self.vals[:, n - 1])
        for i, (k, lab, c) in enumerate(self.KEYS):
            v = self.vals[i, n - 1]
            if lab in ("Flaring", "Other"):
                self.lbl[i].set_text("")
                continue
            ypos = (cum[i] - v / 2) / 42
            self.lbl[i].set_position((0.865, 0.14 + 0.66 * ypos - 0.012))
            self.lbl[i].set_text(f"{lab}  {v:.1f}")
        self.total.set_text(f"{cum[-1]:.1f} Gt")
        self.totl.set_text(f"in {int(self.yr[n - 1])}")


class _Group:
    def __init__(self, items):
        self.items = items

    def remove(self):
        for i in self.items:
            i.remove()


COUNTRY_COLORS = {
    "United States": "#5a8fe6", "China": "#e5554f", "Russia": "#b07fe0", "Germany": "#e6c35a", "United Kingdom": "#5ac8d8",
    "Japan": "#f08aa8", "India": "#f39a3d", "France": "#7da7ff", "Canada": "#d65a5a", "Ukraine": "#e8d36a",
    "Poland": "#c98be0", "Italy": "#69c98d", "South Africa": "#c9a26b", "Mexico": "#7fd1a2", "Iran": "#6fc1b0",
    "South Korea": "#9fb0ff", "Australia": "#ffb36b", "Brazil": "#5fd17a", "Saudi Arabia": "#a3c96b", "Spain": "#f2a07b",
    "Belgium": "#b8b8b8", "Netherlands": "#ff9f4a", "Kazakhstan": "#7ab8ff", "Czechia": "#a0a0d0", "Indonesia": "#d0a0a0",
}


class BarRace(MplScene):
    N = 12

    def setup(self):
        c = data.owid_countries()
        piv = c.pivot_table(index="year", columns="country", values="cumulative_co2").loc[1850:2024].ffill().fillna(0) / 1000
        self.piv = piv
        self.ax = self.fig.add_axes([0.20, 0.10, 0.70, 0.72])
        ax = self.ax
        ax.grid(axis="y", visible=False)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        self.year_txt = self.fig.text(0.93, 0.15, "", fontsize=110, color="#2a3346", ha="right", fontweight="bold")
        _title(self.fig, "The running total", "Cumulative CO$_2$ from fossil fuels and cement since 1750, billion tonnes")
        self.fig.text(0.057, 0.035, "Data: Global Carbon Budget via Our World in Data", color=M, fontsize=19)

    def state(self, yr):
        y0 = int(np.floor(yr))
        y1 = min(y0 + 1, 2024)
        f = yr - y0
        v = self.piv.loc[y0] * (1 - f) + self.piv.loc[y1] * f
        return v.sort_values(ascending=False)

    def draw(self, t):
        final = self.p.get("mode") == "final"
        yr = 2024.0 if final else lerp(1850, 2024, min(t / (0.92 * self.dur), 1))
        v = self.state(yr)
        top = v.iloc[: self.N + 2]
        ax = self.ax
        ax.cla()
        ax.grid(axis="x", color="#1c2433")
        ax.grid(axis="y", visible=False)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        # smooth rank positions: rank = number of countries with larger value (continuous)
        vmax = max(top.iloc[0], 1e-3)
        for i, (name, val) in enumerate(top.items()):
            if i >= self.N:
                break
            col = COUNTRY_COLORS.get(name, "#8899aa")
            alpha = 1.0
            if final and name not in ("United States", "China"):
                alpha = lerp(1.0, 0.45, ramp(t, 2.0, 1.5))
            ax.barh(i, val, color=col, height=0.78, alpha=alpha)
            ax.text(-vmax * 0.012, i, name, ha="right", va="center", fontsize=25, color="white", alpha=alpha)
            ax.text(val + vmax * 0.01, i, f"{val:,.0f}", ha="left", va="center", fontsize=23, color=M, alpha=alpha)
        ax.set_ylim(self.N - 0.4, -0.6)
        ax.set_xlim(0, vmax * 1.13)
        ax.set_yticks([])
        self.year_txt.set_text(f"{int(yr)}")


class PerCapita(MplScene):
    PICK = ["Saudi Arabia", "Australia", "United States", "Canada", "Russia", "South Korea", "China", "Japan", "Germany",
            "World", "United Kingdom", "France", "Brazil", "Indonesia", "India", "Nigeria", "Ethiopia"]

    def setup(self):
        o = data.owid()
        d = o[(o.year == 2024) & o.country.isin(self.PICK)].set_index("country").co2_per_capita
        self.v = d.reindex(self.PICK).sort_values(ascending=True)
        self.ax = self.fig.add_axes([0.22, 0.09, 0.70, 0.74])
        ax = self.ax
        ax.grid(axis="y", visible=False)
        ax.spines["left"].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.set_xlim(0, 23)
        ax.set_ylim(-0.6, len(self.v) - 0.4)
        ax.set_yticks(range(len(self.v)), [n if n != "World" else "World average" for n in self.v.index], fontsize=24)
        cols = [A if n in ("United States", "China", "India") else ("#ffffff" if n == "World" else "#6d7f9e") for n in self.v.index]
        self.bars = ax.barh(range(len(self.v)), np.zeros(len(self.v)), color=cols, height=0.72)
        self.txt = [ax.text(0, i, "", va="center", fontsize=22, color=M) for i in range(len(self.v))]
        _title(self.fig, "Per person", "Tonnes of CO$_2$ from fossil fuels and industry per person, 2024")
        self.fig.text(0.057, 0.035, "Data: Global Carbon Budget via Our World in Data", color=M, fontsize=19)

    def draw(self, t):
        for i, (b, val) in enumerate(zip(self.bars, self.v.values)):
            k = ease_out((t - 0.4 - 0.12 * (len(self.v) - i)) / 1.2)
            b.set_width(val * max(k, 0))
            self.txt[i].set_position((val * max(k, 0) + 0.25, i))
            self.txt[i].set_text(f"{val:.1f}" if k > 0.95 else "")


class FuelBars(MplScene):
    KEYS = EmissionsArea.KEYS

    def setup(self):
        w = data.owid_world().loc[2024]
        self.v = [(lab, w[k] / 1000, c) for k, lab, c in self.KEYS]
        self.ax = self.fig.add_axes([0.07, 0.14, 0.86, 0.64])
        ax = self.ax
        ax.set_ylim(0, 18.5)
        ax.set_xlim(-0.6, len(self.v) - 0.4)
        ax.set_xticks(range(len(self.v)), [l for l, _, _ in self.v], fontsize=28)
        ax.set_ylabel("Billion tonnes CO$_2$, 2024")
        self.bars = ax.bar(range(len(self.v)), [0] * len(self.v), color=[c for _, _, c in self.v], width=0.66)
        self.txt = [ax.text(i, 0, "", ha="center", va="bottom", fontsize=34, color="white") for i in range(len(self.v))]
        tot = sum(x for _, x, _ in self.v)
        self.fig.text(0.93, 0.76, f"Total {tot:.1f} Gt", ha="right", fontsize=44, color="white", fontweight="light")
        _title(self.fig, "What we burn", "Global CO$_2$ emissions by source, 2024")
        self.fig.text(0.057, 0.035, "Data: Global Carbon Budget via Our World in Data", color=M, fontsize=19)

    def draw(self, t):
        for i, (b, (lab, val, c)) in enumerate(zip(self.bars, self.v)):
            k = ease_out((t - 0.5 - 0.5 * i) / 1.5)
            b.set_height(val * max(k, 0))
            self.txt[i].set_position((i, val * max(k, 0) + 0.25))
            self.txt[i].set_text(f"{val:.1f}" if k > 0.2 else "")


def _stripe_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("stripes", ["#08306b", "#2171b5", "#6baed6", "#f7f7f7", "#fc9272", "#de2d26", "#67000d"])


class Stripes(MplScene):
    def setup(self):
        g = data.gistemp()
        self.yr, self.v = g.year.values, g.anom.values
        self.cmap = _stripe_cmap()
        self.ax = self.fig.add_axes([0.0, 0.0, 1.0, 1.0])
        ax = self.ax
        ax.axis("off")
        ax.set_xlim(self.yr[0] - 0.5, self.yr[-1] + 0.5)
        ax.set_ylim(0, 1)
        self.rects = []
        for y, v in zip(self.yr, self.v):
            r = Rectangle((y - 0.5, 0), 1.0, 1.0, color=self.cmap((v + 0.75) / 2.1), lw=0, alpha=0)
            ax.add_patch(r)
            self.rects.append(r)
        self.lab = self.fig.text(0.5, 0.08, "", fontsize=60, color="white", ha="center", fontweight="light")
        self.t1 = self.fig.text(0.04, 0.08, "1880", fontsize=34, color="white", alpha=0)
        self.t2 = self.fig.text(0.96, 0.08, "2025", fontsize=34, color="white", ha="right", alpha=0)
        self.src = self.fig.text(0.04, 0.03, "Data: NASA GISTEMP v4 global surface temperature anomaly (vs 1951–1980)", fontsize=19, color="white", alpha=0)

    def draw(self, t):
        span = 0.7 * self.dur
        n = len(self.rects)
        for i, r in enumerate(self.rects):
            r.set_alpha(min(max((t - span * i / n) / 0.4, 0), 1))
        k = min(int(n * min(t / span, 1)), n - 1)
        self.lab.set_text(f"{self.yr[k]}   {self.v[k]:+.2f} °C" if t < span + 1.0 else "")
        a = ramp(t, span + 1.0, 1.0)
        for x in (self.t1, self.t2, self.src):
            x.set_alpha(a)


class TempLine(MplScene):
    def setup(self):
        g = data.gistemp()
        self.yr, self.v = g.year.values, g.anom.values
        self.off = -g[(g.year >= 1880) & (g.year <= 1900)].anom.mean()  # shift to an 1880–1900 baseline
        self.ax = self.fig.add_axes([0.08, 0.14, 0.82, 0.66])
        ax = self.ax
        cm = _stripe_cmap()
        ax.bar(self.yr, self.v, color=[cm((x + 0.75) / 2.1) for x in self.v], width=0.9, alpha=0.55)
        sm = np.convolve(self.v, np.ones(5) / 5, mode="same")
        sm[:2] = sm[-2:] = np.nan
        self.ln, = ax.plot([], [], color="white", lw=3.5)
        self.sm = sm
        ax.set_xlim(1878, 2027)
        ax.set_ylim(-0.7, 1.75)
        ax.axhline(0, color=hexc(DIM), lw=1.2)
        ax.set_ylabel("°C vs 1951–1980")
        ax2 = ax.twinx()
        ax2.set_ylim(-0.7 + self.off, 1.75 + self.off)
        ax2.set_ylabel("°C vs 1880–1900 (≈ pre-industrial)", color=M)
        ax2.grid(False)
        ax2.spines["right"].set_visible(True)
        self.ax2 = ax2
        i = int(np.argmax(self.v))
        ax.annotate(f"{self.yr[i]}: {self.v[i]:+.2f} °C\n(≈ {self.v[i] + self.off:+.2f} °C vs 1880–1900)",
                    xy=(self.yr[i], self.v[i]), xytext=(1990, 1.5), fontsize=26, color="white",
                    arrowprops=dict(arrowstyle="-", color="white", lw=1.4), va="center", ha="right")
        if self.p.get("paris"):
            for lvl, lab in [(1.5, "1.5 °C"), (2.0, "2 °C")]:
                ax2.axhline(lvl, color=A if lvl == 1.5 else RED and hexc(RED), lw=2, ls=(0, (8, 6)))
                ax2.text(1882, lvl + 0.03, f"Paris Agreement · {lab} above pre-industrial", color=A if lvl == 1.5 else hexc(RED), fontsize=22, va="bottom")
            ax2.set_ylim(-0.7 + self.off, 2.25)
            ax.set_ylim(-0.7, 2.25 - self.off)
        _title(self.fig, "Global surface temperature", "Annual anomaly, with 5-year average")
        self.fig.text(0.057, 0.035, "Data: NASA GISTEMP v4. Right axis re-baselined to 1880–1900 as an approximate pre-industrial reference.", color=M, fontsize=19)

    def draw(self, t):
        k = ease_io(min(t / (0.6 * self.dur), 1))
        n = int(1 + k * (len(self.yr) - 1))
        self.ln.set_data(self.yr[:n], self.sm[:n])


class Co2Temp(MplScene):
    def setup(self):
        a = data.mlo_annual().set_index("year")["mean"]
        g = data.gistemp().set_index("year").anom
        j = a.index.intersection(g.index)
        self.x, self.y, self.yr = a.loc[j].values, g.loc[j].values, j.values
        self.ax = self.fig.add_axes([0.09, 0.14, 0.84, 0.66])
        ax = self.ax
        ax.set_xlim(310, 432)
        ax.set_ylim(-0.35, 1.45)
        ax.set_xlabel("CO$_2$ at Mauna Loa, annual mean (ppm)")
        ax.set_ylabel("Global temperature anomaly (°C)")
        self.sc = ax.scatter([], [], s=90, c=[], cmap="plasma", vmin=1959, vmax=2025)
        cf = np.polyfit(self.x, self.y, 1)
        self.cf = cf
        self.fit, = ax.plot([], [], color="white", lw=2.5, ls=(0, (6, 4)))
        self.yt = ax.text(315, 1.25, "", fontsize=50, color="white", fontweight="light")
        r = np.corrcoef(self.x, self.y)[0, 1]
        self.rt = ax.text(428, -0.25,  f"≈ {cf[0] * 100:.2f} °C per 100 ppm · correlation r = {r:.2f}", fontsize=24, color=M, alpha=0, ha="right")
        _title(self.fig, "Carbon dioxide and temperature", "Each dot is one year, 1959–2025")
        self.fig.text(0.057, 0.035, "Data: NOAA GML / Scripps (CO$_2$), NASA GISTEMP v4 (temperature)", color=M, fontsize=19)

    def draw(self, t):
        k = ease_io(min(t / (0.65 * self.dur), 1))
        n = int(1 + k * (len(self.x) - 1))
        self.sc.set_offsets(np.c_[self.x[:n], self.y[:n]])
        self.sc.set_array(self.yr[:n].astype(float))
        self.yt.set_text(str(self.yr[n - 1]))
        a = ramp(t, 0.68 * self.dur, 1.0)
        if a > 0:
            xs = np.array([312, 430])
            self.fit.set_data(xs, np.polyval(self.cf, xs))
            self.fit.set_alpha(a)
            self.rt.set_alpha(a)
