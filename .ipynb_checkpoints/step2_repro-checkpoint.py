import os
import json
from helpers import load_config, abs_path, get_obs_mode, REPO_DIR

config = load_config()
script_dir = abs_path(config['info_dict']['script_dir'])
reppro_dir = abs_path(config['info_dict']['reppro_dir'])
cluster_directory = abs_path(config['info_dict']['cluster_directory'])
flag_file = os.path.join(REPO_DIR, 'update_flag.py')
# Compute relative path from cluster_directory to reppro_dir
# This handles paths correctly regardless of how they're stored (./, absolute, etc.)
reppro_dir_relative = os.path.relpath(reppro_dir, cluster_directory)

#script: preprocess the data with chandra_repro
script = open(os.path.join(script_dir, 'preprocess_data.sh'), 'w')
script.write(f'cd {cluster_directory}\n')
script.write('source ~/miniforge3/etc/profile.d/conda.sh\n')
script.write('conda activate ciao\n')

for obs_id in config["info_dict"]["obs_ids"]:
    script.write(f'rm -rf {reppro_dir}/{obs_id}\n')
    mode_obs_id = get_obs_mode(obs_id)
    if mode_obs_id == 'VFAINT':
        script.write(f'chandra_repro {obs_id} check_vf_pha=yes verbose=1 outdir = {reppro_dir_relative}/{obs_id} clobber = yes\n')
    else:
        script.write(f'chandra_repro {obs_id} verbose=1 outdir = {reppro_dir_relative}/{obs_id} clobber = yes\n')

    script.write('punlearn ardlib\n')

    script.write(f'python3 {flag_file} reprocessed\n')


script.close()
