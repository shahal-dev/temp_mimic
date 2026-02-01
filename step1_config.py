import os
import json

filename = "config.json"

config = {
    'info_dict': {},
    'flags': {},
}

inp = input("Do you want to start from scratch? (y/n): ")
if inp == 'y':
    name = input("Enter the name of the cluster(e.g. Perseus): ")
    sn_per_region = int(input("Enter the number of SNs per region(e.g. 10): "))
    reg_smoothness = float(input("Enter the smoothness of the regions(e.g. 0.1): "))
    cluster_directory = input('Enter the directory path for the downloaded data(e.g. /path/to/cluster_data): ') 
    parent_directory = input('Enter the directory path for the parent directory(e.g. /path/to/parent_directory): ')

    config['info_dict']['name'] = name
    config['info_dict']['sn_per_region'] = sn_per_region
    config['info_dict']['reg_smoothness'] = reg_smoothness
    # Normalize paths to remove ./ prefix and clean up path format
    config['info_dict']['cluster_directory'] = os.path.normpath(cluster_directory)
    config['info_dict']['parent_directory'] = os.path.normpath(parent_directory)

    parent_directory = os.path.join(config['info_dict']['parent_directory'], name)
    if not os.path.exists(parent_directory):
        os.makedirs(parent_directory)

    reppro_dir = os.path.join(parent_directory, 'reprocessed_data')
    merge_dir = os.path.join(parent_directory, f'merge_{name}_{reg_smoothness}_{sn_per_region}')
    spec_file_dir = os.path.join(parent_directory, 'spec_files')
    region_file_dir = os.path.join(parent_directory, 'region_files')
    map_file_dir = os.path.join(parent_directory, 'map_files')
    
    os.makedirs(reppro_dir, exist_ok=True)
    os.makedirs(merge_dir, exist_ok=True)
    os.makedirs(spec_file_dir, exist_ok=True)
    os.makedirs(region_file_dir, exist_ok=True)
    os.makedirs(map_file_dir, exist_ok=True)

    # Normalize all directory paths before storing
    config['info_dict']['reppro_dir'] = os.path.normpath(reppro_dir)
    config['info_dict']['merge_dir'] = os.path.normpath(merge_dir)
    config['info_dict']['spec_file_dir'] = os.path.normpath(spec_file_dir)
    config['info_dict']['region_file_dir'] = os.path.normpath(region_file_dir)
    config['info_dict']['map_file_dir'] = os.path.normpath(map_file_dir)


    with open(filename, 'w') as f:
        json.dump(config, f, indent=4)
else:
    with open(filename, 'r') as f:
        config = json.load(f)   
    parent_directory = config['info_dict']['parent_directory']
    name = config['info_dict']['name']
    sn_per_region = config['info_dict']['sn_per_region']
    reg_smoothness = config['info_dict']['reg_smoothness']
    cluster_directory = config['info_dict']['cluster_directory']
    
    parent_directory = os.path.join(parent_directory, name)

    reppro_dir = os.path.join(parent_directory, 'reprocessed_data')
    merge_dir = os.path.join(parent_directory, f'merge_{name}_{reg_smoothness}_{sn_per_region}')
    spec_file_dir = os.path.join(parent_directory, 'spec_files')
    region_file_dir = os.path.join(parent_directory, 'region_files')
    map_file_dir = os.path.join(parent_directory, 'map_files')

    if not os.path.exists(reppro_dir):
        os.makedirs(reppro_dir)
    if not os.path.exists(merge_dir):
        os.makedirs(merge_dir)
    if not os.path.exists(spec_file_dir):
        os.makedirs(spec_file_dir)
    if not os.path.exists(region_file_dir):
        os.makedirs(region_file_dir)
    if not os.path.exists(map_file_dir):
        os.makedirs(map_file_dir)

    # Normalize all directory paths before storing
    config['info_dict']['reppro_dir'] = os.path.normpath(reppro_dir)
    config['info_dict']['merge_dir'] = os.path.normpath(merge_dir)
    config['info_dict']['spec_file_dir'] = os.path.normpath(spec_file_dir)
    config['info_dict']['region_file_dir'] = os.path.normpath(region_file_dir)
    config['info_dict']['map_file_dir'] = os.path.normpath(map_file_dir)



config['flags']['reprocessed'] = False
config['flags']['flare_filtered'] = False
config['flags']['merge_data'] = False
config['flags']['flux_maps'] = False
config['flags']['remove_point_source'] = False
config['flags']['countour_binning'] = False
config['flags']['convert_region_coordinates'] = False
config['flags']['extract_spectra'] = False
config['flags']['xspec_fitting'] = False
config['flags']['parse_results'] = False
config['flags']['maps_created'] = False


config["info_dict"]["obs_ids"] = []
for folder in os.listdir(config["info_dict"]["cluster_directory"]):
    obs_id = folder.split()[0]
    config["info_dict"]["obs_ids"].append(obs_id)
script_dir = os.path.join(config['info_dict']['parent_directory'], config["info_dict"]["name"], 'scripts')
config['info_dict']['script_dir'] = os.path.normpath(script_dir)

with open('config.json', 'w') as f:
    json.dump(config, f, indent=4)

os.makedirs(script_dir, exist_ok=True)



print(f"Cluster information saved to {filename}")
