"""Loaders for the public datasets used in the film."""
import functools
import os

import numpy as np
import pandas as pd

from common_paths import CACHE, DATA


@functools.lru_cache(None)
def mlo_monthly():
    m = pd.read_csv(os.path.join(DATA, "co2-mm-mlo.csv"), header=None, skiprows=1,
                    names=["date", "dec", "avg", "deseas", "nd", "sd", "unc"])
    m = m[m.avg > 0].copy()
    m["year"] = m.date.str[:4].astype(int)
    m["month"] = m.date.str[5:7].astype(int)
    return m


@functools.lru_cache(None)
def global_monthly():
    g = pd.read_csv(os.path.join(DATA, "co2-mm-gl.csv"), header=None, skiprows=1,
                    names=["date", "dec", "avg", "unc", "trend", "tunc"])
    return g[g.avg > 0].copy()


@functools.lru_cache(None)
def mlo_annual():
    a = pd.read_csv(os.path.join(DATA, "co2-annmean-mlo.csv"))
    a.columns = ["year", "mean", "unc"]
    a["inc"] = a["mean"].diff()
    return a


@functools.lru_cache(None)
def gistemp():
    t = pd.read_csv(os.path.join(DATA, "annual.csv"))
    g = t[t.Source == "GISTEMP"].sort_values("Year")
    return g[["Year", "Mean"]].rename(columns={"Year": "year", "Mean": "anom"}).reset_index(drop=True)


@functools.lru_cache(None)
def owid():
    return pd.read_csv(os.path.join(DATA, "owid-co2-data.csv"))


def owid_world():
    o = owid()
    return o[o.country == "World"].set_index("year")


def owid_countries():
    o = owid()
    return o[o.iso_code.notna() & ~o.iso_code.astype(str).str.startswith("OWID")]


@functools.lru_cache(None)
def npz(name):
    return dict(np.load(os.path.join(CACHE, name), allow_pickle=False))
