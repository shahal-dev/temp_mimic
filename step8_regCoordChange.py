import os
from helpers import load_config, abs_path, REPO_DIR, get_num_of_only_files
config = load_config()
script_dir = abs_path(config['info_dict']['script_dir'])
merge_dir = abs_path(config['info_dict']['merge_dir'])
map_file_dir = abs_path(config['info_dict']['map_file_dir'])
out_reg_dir = abs_path(os.path.join(config['info_dict']['spec_file_dir'],f"contbin_sn{config['info_dict']['sn_per_region']}_smooth{config['info_dict']['reg_smoothness']}",'outreg'))

script = open(os.path.join(script_dir, 'regCoordChange.sh'), 'w') 
script.write(f'Xvfb :1234 -screen 0 1024x768x24 &\nserverpid=$!\n')
script.write(f'DISPLAY=:1234 ds9 {merge_dir}/scaled_broad_flux_final.fits &\nsleep 5\nxpaset -p ds9 lower\n')
for file in range(get_num_of_only_files(out_reg_dir)):
    script.write(f'''
xpaset -p ds9 regions load {out_reg_dir}/xaf_{str(file)}.reg
xpaset -p ds9 regions format ciao
xpaset -p ds9 regions systems wcs
xpaset -p ds9 skyformat sexagesimal
xpaset -p ds9 regions save {out_reg_dir}/sex/xaf_{str(file)}.reg
xpaset -p ds9 regions delete all
    ''')
script.write(f'xpaset -p ds9 exit')
script.write(f'kill $serverpid')
script.write(f'python3 {REPO_DIR}/update_flag.py convert_region_coordinates')
script.close()

print(f"Script created successfully: {script.name}")
    