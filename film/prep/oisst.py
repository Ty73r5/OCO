"""NOAA OISST v2.1 daily SST anomaly (public AWS bucket) sampled through the 2015-16 El Nino."""
import datetime as dt
import io
import os
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import h5netcdf
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common_paths import CACHE  # noqa: E402

BASE = "https://noaa-cdr-sea-surface-temp-optimum-interpolation-pds.s3.amazonaws.com/data/v2.1/avhrr"


def fetch(d):
    url = f"{BASE}/{d:%Y%m}/oisst-avhrr-v02r01.{d:%Y%m%d}.nc"
    for _ in range(4):
        try:
            raw = urllib.request.urlopen(url, timeout=120).read()
            break
        except Exception as e:
            err = e
    else:
        print("fail", d, err)
        return d, None
    with h5netcdf.File(io.BytesIO(raw), "r") as f:
        v = f.variables["anom"]
        a = v[0, 0].astype(np.float32)
        a = np.where(a == v.attrs["_FillValue"], np.nan, a * v.attrs.get("scale_factor", 1.0) + v.attrs.get("add_offset", 0.0))
    return d, a.astype(np.float16)


if __name__ == "__main__":
    start, end, step = dt.date(2014, 6, 1), dt.date(2016, 12, 31), 4
    dates = []
    d = start
    while d <= end:
        dates.append(d)
        d += dt.timedelta(days=step)
    with ThreadPoolExecutor(8) as ex:
        res = [r for r in ex.map(fetch, dates) if r[1] is not None]
    np.savez_compressed(os.path.join(CACHE, "oisst_anom_2014_2016.npz"),
                        anom=np.stack([r[1] for r in res]), dates=np.array([r[0].isoformat() for r in res]))
    print("done", len(res))
