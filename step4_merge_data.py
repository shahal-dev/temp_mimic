from helpers import load_config, abs_path, REPO_DIR
import os
print(REPO_DIR)
config = load_config()
script_dir = abs_path(config['info_dict']['script_dir'])
reppro_dir = abs_path(config['info_dict']['reppro_dir'])
merge_dir = abs_path(config['info_dict']['merge_dir'])

#script: merge the data
script = open(os.path.join(script_dir, 'merge_data.sh'), 'w')
script.write(f'cd ../reprocessed_data \n')
script.write(f'pwd \n')
script.write(f'find "$PWD" -type f -name "acisf*clean*" >clean_evt.list\n')
script.write(f'punlearn merge_obs\nmerge_obs @clean_evt.list {merge_dir}/ bin=1 bands=broad clobber=yes\n')

script.write(f'python3 {REPO_DIR}/update_flag.py merge_data\n')
script.write(f'echo "Merging data for {config["info_dict"]["name"]}"\n') 
