"""Shared paths. Large data and intermediate media live outside the repo."""
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("OCO_WORK", "/tmp/claude-0/-home-user-OCO/0ed38738-5a83-580d-a460-36a42f55469e/scratchpad")
DATA = os.path.join(WORK, "data")
CACHE = os.path.join(WORK, "cache")
MEDIA = os.path.join(WORK, "media")
MODELS = os.path.join(WORK, "models")
FONTS = os.path.join(WORK, "fonts")
for _d in (DATA, CACHE, MEDIA, MODELS, FONTS):
    os.makedirs(_d, exist_ok=True)
