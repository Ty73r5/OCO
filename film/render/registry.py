"""Maps script visual names to scene classes."""
import importlib

REG = {
    "globe": "render.globe:GlobeScene",
    "goes_day": "render.goes_scene:GoesDay",
    "keeling": "render.charts:Keeling",
    "seasonal": "render.charts:Seasonal",
    "amplitude": "render.charts:Amplitude",
    "growth_bars": "render.charts:GrowthBars",
    "emissions_area": "render.charts:EmissionsArea",
    "bar_race": "render.charts:BarRace",
    "per_capita": "render.charts:PerCapita",
    "fuel_bars": "render.charts:FuelBars",
    "stripes": "render.charts:Stripes",
    "temp_line": "render.charts:TempLine",
    "co2_temp": "render.charts:Co2Temp",
    "starfield": "render.diagrams:Starfield",
    "title": "render.diagrams:Title",
    "chapter_card": "render.diagrams:ChapterCard",
    "text_card": "render.diagrams:TextCard",
    "counter_intro": "render.diagrams:CounterIntro",
    "counter_final": "render.diagrams:CounterFinal",
    "credits": "render.diagrams:Credits",
    "ppm_grid": "render.diagrams:PpmGrid",
    "stations": "render.diagrams:Stations",
    "timeline": "render.diagrams:Timeline",
    "launch": "render.diagrams:Launch",
    "atrain": "render.diagrams:ATrain",
    "lightpath": "render.diagrams:LightPath",
    "spectrum": "render.diagrams:Spectrum",
    "precision": "render.diagrams:Precision",
    "footprints": "render.diagrams:Footprints",
    "million": "render.diagrams:Million",
    "retrieval": "render.diagrams:Retrieval",
    "modes": "render.diagrams:Modes",
    "sif": "render.diagrams:Sif",
    "tropics": "render.diagrams:Tropics",
    "la_dome": "render.diagrams:LaDome",
    "fire_total": "render.diagrams:FireTotal",
    "budget": "render.diagrams:Budget",
    "sst": "render.maps:Sst",
    "ch4": "render.maps:Ch4",
    "no2": "render.maps:No2",
    "co_fire": "render.maps:CoFire",
}


def make(sc, dur):
    mod, cls = REG[sc["visual"]].split(":")
    return getattr(importlib.import_module(mod), cls)(sc, dur)
