"""Composite Sentinel-5P TROPOMI Level-2 COGs (meeo-s5p public bucket) onto a global grid.

Reads only a reduced-resolution overview of each orbit via HTTP range requests.
Usage: python s5p.py CH4|CO|NO2 ...
"""
import datetime as dt
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import rasterio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common_paths import CACHE  # noqa: E402
from prep.s3list import list_keys  # noqa: E402

os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "4")
BUCKET = "meeo-s5p"
PRODUCTS = {
    "CH4": ("L2__CH4___", "PRODUCT_methane_mixing_ratio_bias_corrected_4326.tif", 0.5),
    "CO": ("L2__CO____", "PRODUCT_carbonmonoxide_total_column_4326.tif", 0.5),
    "NO2": ("L2__NO2___", "PRODUCT_nitrogendioxide_tropospheric_column_4326.tif", 0.75),
}


def read_orbit(key, var_suffix, qa_min, level, res, bbox):
    base = f"/vsicurl/https://{BUCKET}.s3.amazonaws.com/" + key
    try:
        with rasterio.open(base, overview_level=level) as d:
            v = d.read(1).astype(np.float32)
            tr = d.transform
        with rasterio.open(base.replace(var_suffix, "PRODUCT_qa_value_4326.tif"), overview_level=level) as d:
            qa = d.read(1).astype(np.float32)
    except Exception as e:  # missing file or transient error
        print("skip", key[-90:], e, flush=True)
        return None
    if qa.shape != v.shape:
        return None
    qmax = np.nanmax(qa)
    qa = qa / 100.0 if qmax > 1.5 else qa
    ok = (v > -9000) & np.isfinite(v) & (qa >= qa_min)
    r, c = np.nonzero(ok)
    lon = tr.c + (c + 0.5) * tr.a
    lat = tr.f + (r + 0.5) * tr.e
    lon0, lat0, lon1, lat1 = bbox
    sel = (lon >= lon0) & (lon < lon1) & (lat >= lat0) & (lat < lat1)
    gi = ((lat1 - lat[sel]) / res).astype(np.int32)
    gj = ((lon[sel] - lon0) / res).astype(np.int32)
    return gi, gj, v[r[sel], c[sel]]


def composite(name, dates, out, level=0, res=0.1, bbox=(-180, -90, 180, 90), utc_hours=None, daily=False):
    prod, suffix, qa_min = PRODUCTS[name]
    if name == "CH4":
        # Bias-corrected COG may not exist in every processor version; fall back to raw.
        pass
    ny, nx = int(round((bbox[3] - bbox[1]) / res)), int(round((bbox[2] - bbox[0]) / res))
    keys = []
    for d in dates:
        ks = list_keys(BUCKET, f"COGT/OFFL/{prod}/{d:%Y/%m/%d}/")
        sfx = suffix
        if name == "CH4" and not any(k.endswith(sfx) for k in ks):
            sfx = "PRODUCT_methane_mixing_ratio_4326.tif"
        for k in ks:
            if not k.endswith(sfx):
                continue
            if utc_hours is not None:
                t = os.path.basename(k).split("_")
                start = [s for s in t if "T" in s and s[:8].isdigit()][0]
                hh = int(start[9:11])
                if hh not in utc_hours:
                    continue
            keys.append((d, k, sfx))
    print(name, len(keys), "orbits", flush=True)
    if daily:
        days = sorted(set(d for d, _, _ in keys))
        stack_s = np.zeros((len(days), ny, nx), np.float32)
        stack_n = np.zeros((len(days), ny, nx), np.uint16)
    s = np.zeros((ny, nx), np.float64)
    n = np.zeros((ny, nx), np.uint32)

    def job(item):
        d, k, sfx = item
        return d, read_orbit(k, sfx, qa_min, level, res, bbox)

    with ThreadPoolExecutor(12) as ex:
        for i, (d, res_) in enumerate(ex.map(job, keys)):
            if res_ is None:
                continue
            gi, gj, v = res_
            gi = np.clip(gi, 0, ny - 1)
            gj = np.clip(gj, 0, nx - 1)
            np.add.at(s, (gi, gj), v)
            np.add.at(n, (gi, gj), 1)
            if daily:
                di = days.index(d)
                np.add.at(stack_s[di], (gi, gj), v)
                np.add.at(stack_n[di], (gi, gj), 1)
            if i % 50 == 0:
                print(name, i, "/", len(keys), flush=True)
    mean = np.where(n > 0, s / np.maximum(n, 1), np.nan).astype(np.float32)
    extra = {}
    if daily:
        extra["daily"] = np.where(stack_n > 0, stack_s / np.maximum(stack_n, 1), np.nan).astype(np.float32)
        extra["days"] = np.array([d.isoformat() for d in days])
    np.savez_compressed(out, mean=mean, count=n, bbox=np.array(bbox), res=res, **extra)
    print("wrote", out, flush=True)


def daterange(a, b, step=1):
    d = a
    while d <= b:
        yield d
        d += dt.timedelta(days=step)


if __name__ == "__main__":
    which = sys.argv[1]
    D = dt.date
    if which == "CH4":
        # Northern summer + autumn 2024 for broad coverage of methane hotspots.
        composite("CH4", list(daterange(D(2024, 5, 1), D(2024, 10, 31), 2)), os.path.join(CACHE, "s5p_ch4_2024.npz"), level=0, res=0.1)
    elif which == "CO":
        # June 2023 Canadian wildfire smoke, daily maps over North America and the Atlantic.
        composite("CO", list(daterange(D(2023, 5, 28), D(2023, 6, 14))), os.path.join(CACHE, "s5p_co_2023_canada.npz"),
                  level=0, res=0.1, bbox=(-170, 10, 20, 80), utc_hours=set(range(13, 24)), daily=True)
    elif which == "NO2":
        # Northern winter, when NO2 lives longest and city plumes stand out.
        composite("NO2", list(daterange(D(2024, 11, 15), D(2025, 2, 15), 3)), os.path.join(CACHE, "s5p_no2_winter.npz"), level=0, res=0.07)
    elif which == "CO_GLOBAL":
        composite("CO", list(daterange(D(2024, 8, 1), D(2024, 9, 30), 3)), os.path.join(CACHE, "s5p_co_global_2024.npz"), level=1, res=0.15)
