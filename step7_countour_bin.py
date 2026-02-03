#! /usr/bin/env python3
from astropy.io import fits
import re
from helpers import load_config, abs_path, REPO_DIR
import os
config = load_config()

hdul = fits.open(os.path.join(abs_path(config['info_dict']['map_file_dir']), 'scaled_broad_flux_final.fits'))
region = hdul[0].header['DSVAL1']
numbers = re.findall(r'-?\d*\.\d+', region)

center_x, center_y, width, height = map(float, numbers[:4])
min_x, min_y = center_x-(width/2), center_y-(height/2)

script = open(os.path.join(abs_path(config['info_dict']['script_dir']), 'contour_binning.sh'), 'w')

script.write(f'cd {abs_path(config['info_dict']['spec_file_dir'])}\n')

contbin = 'contbin --sn=' + str(config['info_dict']['sn_per_region']) + \
          ' --smoothsn=' + str(config['info_dict']['reg_smoothness']) + \
          f' --constrainfill --constrainval=3. {os.path.join(abs_path(config['info_dict']['map_file_dir']), "scaled_broad_flux_final.fits")}\n' + \
          'mkdir contbin_sn' + str(config['info_dict']['sn_per_region']) + '_smooth' + str(config['info_dict']['reg_smoothness']) + '\n' + \
          'mkdir contbin_sn' + str(config['info_dict']['sn_per_region']) + '_smooth' + str(config['info_dict']['reg_smoothness']) + '/outreg\n' + \
          'mv bin_signal_stats.qdp bin_sn_stats.qdp contbin_binmap.fits contbin_mask.fits ' + \
          'contbin_out.fits contbin_sn.fits contbin_sn' + str(config['info_dict']['sn_per_region']) + '_smooth' + str(config['info_dict']['reg_smoothness']) + '\n' + \
          'cd contbin_sn' + str(config['info_dict']['sn_per_region']) + '_smooth' + str(config['info_dict']['reg_smoothness']) + '\n'
script.write(contbin)

mkregions = f'make_region_files --minx={min_x} --miny={min_y} --bin=1 --outreg=outreg contbin_binmap.fits\n'
script.write(mkregions)
script.write(f'python3 {REPO_DIR}/update_flag.py contour_binning\n')
script.close()