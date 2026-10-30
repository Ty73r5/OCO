"""GOES-19 ABI full-disk true colour (day) blended with clean-IR (night), one frame per hour.

Reads only bands C01/C02/C03/C13 out of the ABI-L2-MCMIPF NetCDF via S3 range requests.
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import h5netcdf
import numpy as np
import s3fs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common_paths import CACHE  # noqa: E402

FS = None
OUT = os.path.join(CACHE, "goes")
os.makedirs(OUT, exist_ok=True)


def block_mean(a, f):
    h, w = a.shape[0] // f * f, a.shape[1] // f * f
    return np.nanmean(a[:h, :w].reshape(h // f, f, w // f, f), axis=(1, 3))


def frame(key, out, f=4):
    global FS
    if os.path.exists(out):
        return out
    FS = FS or s3fs.S3FileSystem(anon=True)
    with FS.open("noaa-goes19/" + key, "rb", block_size=8 * 2**20, cache_type="readahead") as fh, h5netcdf.File(fh, "r") as nc:
        def band(n):
            v = nc.variables[f"CMI_C{n:02d}"]
            raw = v[:]
            a = raw.astype(np.float32)
            fill = v.attrs.get("_FillValue")
            if fill is not None:
                a[raw == fill] = np.nan
            return a * v.attrs.get("scale_factor", 1.0) + v.attrs.get("add_offset", 0.0)
        b, r, nir, ir = band(1), band(2), band(3), band(13)
    b, r, nir, ir = (block_mean(x, f) for x in (b, r, nir, ir))
    g = 0.45 * r + 0.1 * nir + 0.45 * b  # CIMSS "natural" green
    rgb = np.stack([r, g, b], -1)
    rgb = np.clip(rgb, 0, 1) ** (1 / 2.2)
    # contrast curve
    rgb = np.clip((rgb - 0.05) * 1.22, 0, 1)
    sun = np.clip(np.nanmax(rgb, -1) * 3.0, 0, 1)[..., None]
    irn = np.clip((300.0 - ir) / (300.0 - 200.0), 0, 1)[..., None] ** 1.2
    night = np.concatenate([irn * 0.55, irn * 0.62, irn * 0.75], -1)
    img = sun * rgb + (1 - sun) * np.maximum(night, rgb)
    mask = np.isnan(r)[..., None]
    img = np.where(mask, 0, np.nan_to_num(img))
    np.save(out, (np.clip(img, 0, 1) * 255).astype(np.uint8))
    return out


if __name__ == "__main__":
    from prep.s3list import list_keys
    doy = int(sys.argv[1]) if len(sys.argv) > 1 else 265
    jobs = []
    for hh in range(24):
        ks = [k for k in list_keys("noaa-goes19", f"ABI-L2-MCMIPF/2026/{doy:03d}/{hh:02d}/") if k.endswith(".nc")]
        if not ks:
            continue
        for j, k in enumerate(sorted(ks)[::3][:2]):
            jobs.append((k, os.path.join(OUT, f"d{doy}_h{hh:02d}_{j}.npy")))
    print(len(jobs), "frames", flush=True)
    with ProcessPoolExecutor(4) as ex:
        for o in ex.map(frame, *zip(*jobs)):
            print("ok", o, flush=True)
