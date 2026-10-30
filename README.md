# OCO — *The Breathing Planet*

A 32-minute narrated documentary about NASA's Orbiting Carbon Observatory missions (OCO-2 and OCO-3) and the global carbon story they track. Every chart and map in it is rendered directly from public data.

| | |
|---|---|
| **Runtime** | 32 min 26 s · 1920×1080 · 24 fps · H.264 + AAC, with an English subtitle track |
| **Narration** | Kokoro, an open-weight text-to-speech model (voice `af_heart`) |
| **Music** | Ambient score generated procedurally for this film (`film/audio.py`) |

## Chapters

| Time | Chapter |
|---|---|
| 00:00 | Cold open: Earth from GOES-19 on the 2026 September equinox |
| 01:55 | I · The Curve: Keeling, Mauna Loa, 315.71 → 432.34 ppm |
| 05:22 | II · A Failure, and a Second Chance: OCO's 2009 loss and OCO-2's 2014 launch, with real orbit geometry |
| 07:38 | III · Weighing the Air from Space: spectroscopy, the oxygen "ruler", footprints, retrievals, plant fluorescence |
| 12:21 | IV · The Planet Breathes: the seasonal cycle and its growing amplitude, and the record 2024 growth rate |
| 14:43 | V · The Year the Tropics Exhaled: the 2015–16 El Niño in NOAA sea-surface data, and the OCO-2 findings |
| 16:52 | VI · Fingerprints: NO₂ maps of combustion, power plants, the LA CO₂ dome, Yasur volcano, OCO-3 on the ISS |
| 19:34 | VII · The Other Carbon: TROPOMI methane, and the Canadian smoke of June 2023 day by day |
| 22:19 | VIII · Who Put It There: emissions by fuel, a cumulative bar race by country, per-capita emissions |
| 24:40 | IX · Where Half of It Goes: the global carbon budget, ocean and land sinks, national budgets from the atmosphere |
| 26:50 | X · The Heat: GISTEMP stripes, the 1.5 °C line, CO₂ vs temperature |
| 28:17 | XI · One Day on Earth: a full GOES-19 day, optical-flow interpolated |
| 29:20 | XII · The Watch Continues: the international fleet, the 2025 budget threat, the August 2026 Caltech agreement |

A counter in the corner tracks the CO₂ humanity emits while the film plays. It uses 43.2 Gt per year (2024, including land use), which is about 1,370 tonnes per second.

## Data (all public, fetched by the scripts in `film/prep/`)

- **Mauna Loa and global CO₂**: NOAA GML / Scripps, via [`datasets/co2-ppm`](https://github.com/datasets/co2-ppm)
- **Earth imagery**: NOAA GOES-19 ABI L2 MCMIPF full disk for 23 Sep 2026 (`noaa-goes19` on AWS). True color by day, clean-IR by night.
- **Sea-surface temperature anomaly**: NOAA OISST v2.1, 2014–2016 (`noaa-cdr-sea-surface-temp-optimum-interpolation-pds` on AWS)
- **CH₄, NO₂, CO**: Copernicus Sentinel-5P TROPOMI Level-2 COGs (`meeo-s5p` on AWS), composited onto global grids
- **Emissions**: Global Carbon Budget via Our World in Data ([`owid/co2-data`](https://github.com/owid/co2-data))
- **Global temperature**: NASA GISTEMP v4, via [`datasets/global-temp`](https://github.com/datasets/global-temp)
- **Base maps**: Natural Earth

The spectra, the light-path and footprint diagrams, and the retrieval schematic are labelled on screen as illustrative. The OCO-2 orbit tracks are computed from the real orbital elements (705 km, 98.2°, sun-synchronous). The ISS orbit is computed the same way.

**About the OCO video gallery.** `ocov2.jpl.nasa.gov` and the NASA Earthdata archives (GES DISC) could not be reached from the sandbox that produced this film. That means no JPL footage and no OCO-2 Level-2 XCO₂ data are used. Where the film describes OCO-2 results (the 2015–16 El Niño, power plants, Los Angeles, Yasur), the visuals are explanatory graphics citing the published papers, not maps of OCO-2 data. To add real OCO-2 maps, allow `ocov2.jpl.nasa.gov`, `*.earthdata.nasa.gov` and `oco2.gesdisc.eosdis.nasa.gov` in the environment's network settings, provide Earthdata credentials, and add a scene that reads the OCO-2 Lite files.

## Rebuilding

```bash
pip install matplotlib cartopy xarray h5netcdf h5py netCDF4 scipy rasterio s3fs kokoro-onnx soundfile opencv-python-headless
cd film
python prep/oisst.py; python prep/s5p.py CH4; python prep/s5p.py CO; python prep/s5p.py NO2; python prep/goes.py 266
python tts.py          # narration (needs kokoro-v1.0.onnx + voices-v1.0.bin from the kokoro-onnx releases)
python audio.py        # score + mix
python render.py       # scenes → segments → final MP4 with subtitles
python preview.py c1_full 10   # render one frame of a scene for inspection
```

The working directory for large data and media is set by `OCO_WORK` (see `film/common_paths.py`).

| Path | Contents |
|---|---|
| `film/script.py` | Full narration and scene list |
| `film/render/` | Globe renderer, charts, maps, diagrams |
| `film/plan.py` | Timeline built from the narration lengths |
