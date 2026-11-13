# instrument_config.py
import yaml
from pathlib import Path

DEFAULT_CONFIG = {
    "beam_center": [1043.0, 1046.0],
    "rotation_axis": [0, 1, 0],
    "gain": 15,
    "oscillation_range": 1.0,
    "detector_distance": None,
    "wavelength": None,
    "detector": "ADSC",
    "nx": 2048, "ny": 2048,
    "qx": 0.028, "qy": 0.028,
    "untrusted_ellipse": None,
    "untrusted_quadrilateral": None,
    "sepmin": 7.0,
    "cluster_radius": 3.5,
}

def load_config(path: str | None) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if path:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {p}")
        user_cfg = yaml.safe_load(p.read_text()) or {}
        cfg.update(user_cfg)
    return cfg
