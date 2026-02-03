from helpers import load_config, abs_path, REPO_DIR, get_ccd_filter
import os
from glob import glob

print(REPO_DIR)
config = load_config()
script_dir = abs_path(config['info_dict']['script_dir'])
reppro_dir = abs_path(config['info_dict']['reppro_dir'])
merge_dir = abs_path(config['info_dict']['merge_dir'])

# Build merge list with ccd_id filter so only selected chips (ACIS-I or ACIS-S) are merged;
# chip gaps and the other array are excluded (no chip marks in merged image).
list_path = os.path.join(reppro_dir, 'clean_evt.list')
with open(list_path, 'w') as f_list:
    for obs_id in config['info_dict']['obs_ids']:
        obs_dir = os.path.join(reppro_dir, str(obs_id))
        repro_evt = glob(os.path.join(obs_dir, 'acisf*_repro_evt2.fits'))
        clean_evt = glob(os.path.join(obs_dir, 'acisf*clean*'))
        if not repro_evt:
            continue
        ccd_filter = get_ccd_filter(repro_evt[0])
        # Use clean evt path if it exists (after step3), else expected name for when step3 is run
        if clean_evt:
            evt_path = os.path.abspath(clean_evt[0])
        else:
            evt_path = os.path.abspath(os.path.join(obs_dir, f'acisf{obs_id}_clean_evt.fits'))
        f_list.write(f'{evt_path}[ccd_id={ccd_filter}]\n')

# Script: merge the data (merge_obs reads the list we built above with ccd_id filter)
script = open(os.path.join(script_dir, 'merge_data.sh'), 'w')
script.write(f'cd {reppro_dir}\n')
script.write(f'pwd\n')
script.write(f'punlearn merge_obs\nmerge_obs @clean_evt.list {merge_dir}/ bin=1 bands=broad clobber=yes\n')
script.write(f'python3 {os.path.abspath(REPO_DIR)}/update_flag.py merge_data\n')
script.write(f'echo "Merging data for {config["info_dict"]["name"]}"\n') 
