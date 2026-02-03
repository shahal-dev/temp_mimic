'''
Open broad_thresh.img inside merged folder using ds9  and create following region files:

- src_0.5-7-nps-noem.reg:   A region file that contains all cluster emission (eg. a large circle around the cluster that includes the extended emission, 
                            which will be removed and used for the deflaring/high energy rescaling). This would include areas such as the peak of cluster emission as these regions 
                            may contain high energy events you want to consider in this analysis.

- broad_src_0.5-7-pointsources.reg:   A region file that contains all of the pointsources.

- square.reg:   This will eventually crop out all things outside of the region of interest. 

for these three region files
Region : ciao 
Coordinate System: wcs

For getting the value of minx and miny create the following region file
- min_xy.reg: opnen broad_thresh.img in ds9 and open square.reg. Save this as min_xy.reg. Region : ciao, Coordinate System: physical



save these three region files to /regionfiles

'''

from helpers import load_config, abs_path, REPO_DIR
import os
import re
config = load_config()
map_file_dir = abs_path(config['info_dict']['map_file_dir'])
region_file_dir = abs_path(config['info_dict']['region_file_dir'])
min_xy_file = os.path.join(region_file_dir, 'min_xy.reg')

with open(min_xy_file, 'r') as f:
    for line in f:
        if line.startswith('box'):
            box_line = line.strip()
            break
values = re.findall(r'[+-]?\d*\.\d+', box_line)
x_center, y_center, width, height = map(float, values[:4])
x_min = x_center - (width/2)
y_min = y_center - (height/2)
print(x_min, y_min, width, height)

script_dir = abs_path(config['info_dict']['script_dir'])
merge_dir = abs_path(config['info_dict']['merge_dir'])

script = open(os.path.join(script_dir, 'crop_data.sh'), 'w')
script.write(f'echo "Cropping data"\n')
script.write(f'cd {merge_dir}\n')


# remove cluster emission for deflaring / scaling
script.write(
f'dmcopy "broad_thresh.img[exclude sky=region({os.path.join(region_file_dir, "src_0.5-7-nps-noem.reg")})]" broad_thresh_noem.img clobber=yes\n\n'
)

script.write(
f"""
wavdetect infile=broad_thresh_noem.img \
psffile=none \
expfile=broad_thresh.expmap \
outfile=src_0.5-7.fits \
scellfile=scell_0.5-7.fits \
imagefile=imgfile_0.5-7.fits \
defnbkgfile=nbkg_0.5-7.fits \
regfile={region_file_dir}/broad_src_0.5-7.reg \
scales="1 2 4 8 16 32" \
maxiter=3 sigthresh=5e-6 ellsigma=5.0 clobber=yes
"""
)


script.write(f'dmcopy "scaled_broad_flux.fits[exclude sky=region({region_file_dir}/broad_src_0.5-7.reg)]" scaled_broad_flux_cropped.fits clobber=yes\n')

#point sources are now removed.

square_reg = os.path.join(region_file_dir, 'square.reg')
if os.path.exists(square_reg):
    script.write(f'dmcopy "scaled_broad_flux_cropped.fits[sky=region({square_reg})]" scaled_broad_flux_final.fits clobber=yes\n')
else:
    script.write(f'mv scaled_broad_flux_cropped.fits scaled_broad_flux_final.fits\n')

script.write(f'cp scaled_broad_flux_final.fits {map_file_dir}/scaled_broad_flux_final.fits\n')
script.write(f'python3 {REPO_DIR}/update_flag.py remove_point_source\n')