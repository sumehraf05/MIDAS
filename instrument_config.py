"""
instrument_config.py -- per-session/per-instrument parameters for MIDAS.

These values (beam center, rotation axis, gain, oscillation range, detector
distance/wavelength fallbacks, untrusted detector regions) used to be
hardcoded directly in xds_pipeline.py, which meant anyone running on a
different instrument -- or even the same instrument on a different session,
since beam center drifts -- had to hand-edit the pipeline script itself.

Copy instrument_config.yaml, fill in your values, and pass it with
--config path/to/your_config.yaml. Any key you omit falls back to the
UCSC default below.

Requires pyyaml (pip install pyyaml) -- this is a near-universal transitive
dependency of scientific Python environments, so it's unlikely to be a new
install on a system that already runs XDS via conda.
"""

from pathlib import Path

try:
    import yaml
except ImportError as exc:
    raise ImportError(
        "instrument_config.py requires pyyaml. Install it with: "
        "pip install pyyaml"
    ) from exc


DEFAULT_CONFIG = {
    "beam_center": [1043.0, 1046.0],
    "rotation_axis": [0, 1, 0],
    "gain": 15,
    "oscillation_range": 1.0,
    "detector_distance": None,
    "wavelength": None,
    "detector": "ADSC",
    "nx": 2048,
    "ny": 2048,
    "qx": 0.028,
    "qy": 0.028,
    "overload": 65000,
    "untrusted_ellipse": None,
    "untrusted_quadrilateral": None,
    "sepmin": 7.0,
    "cluster_radius": 3.5,
}


def load_config(path: str | None) -> dict:
    """
    Load an instrument config YAML, falling back to DEFAULT_CONFIG for
    any key not present in the file. Pass path=None to use defaults only
    (e.g. when no --config flag was given).
    """
    cfg = dict(DEFAULT_CONFIG)
    if path:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Config file not found: {p}")
        user_cfg = yaml.safe_load(p.read_text()) or {}
        cfg.update(user_cfg)
    return cfg
