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
