import json
import os
import shutil
from glob import glob

# Get the directory where this file lives (repo root)
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(REPO_DIR, "config.json")

def load_config():
    """Load config.json from the repo directory."""
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def abs_path(path):
    """Convert relative path to absolute (relative to repo root)."""
    if os.path.isabs(path):
        return path
    return os.path.abspath(os.path.join(REPO_DIR, path))

def pad_string(string):
    length = len(string)
    n = 5 - length
    padded_string = '0' * n + string

    return padded_string


def get_obs_mode(obs_id):
    """Get observation mode (VFAINT/FAINT) for an obs_id."""
    # If dmkeypar not available, default to FAINT
    if shutil.which("dmkeypar") is None:
        return "FAINT"

    config = load_config()
    cluster_dir = abs_path(config["info_dict"]["cluster_directory"])
    
    pattern = os.path.join(cluster_dir, str(obs_id), "primary", "*evt2.fits.gz")
    matches = glob(pattern)
    if not matches:
        return "FAINT"  # Default if file not found

    evt2 = matches[0]
    out = os.popen(f"dmkeypar {evt2} DATAMODE echo+").read().split()
    return out[0] if out else "FAINT"


# ACIS chip IDs: I = 0,1,2,3 ; S = 4,5,6,7,8,9 (used for ccd_id filter to exclude chip gaps/other array)
ACIS_I_IDS = {0, 1, 2, 3}
ACIS_S_IDS = {4, 5, 6, 7, 8, 9}


def get_ccd_filter(evt_path):
    """
    Return ccd_id filter string for merge_obs: "0:3" (ACIS-I) or "4:9" (ACIS-S).
    Uses the chip array that has more chips in this observation (same logic as ClusterPyXT).
    Reads DETNAM from the event file header (e.g. "ACIS-0123" -> ACIS-I -> "0:3").
    """
    try:
        from astropy.io import fits
        with fits.open(evt_path) as hdul:
            detnam = (hdul[1].header.get("DETNAM") or hdul[0].header.get("DETNAM") or "").strip().upper()
    except Exception:
        return "0:3"  # default to ACIS-I if unreadable

    if not detnam.startswith("ACIS-"):
        return "0:3"
    ids_str = detnam[5:]
    chip_ids = []
    for c in ids_str:
        if c.isdigit():
            chip_ids.append(int(c))
    if not chip_ids:
        return "0:3"

    n_i = sum(1 for c in chip_ids if c in ACIS_I_IDS)
    n_s = sum(1 for c in chip_ids if c in ACIS_S_IDS)
    return "0:3" if n_i >= n_s else "4:9"
