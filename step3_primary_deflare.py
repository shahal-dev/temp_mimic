import os
import json
from helpers import get_obs_mode, load_config, abs_path

config = load_config()
script_dir = abs_path(config['info_dict']['script_dir'])
reppro_dir = abs_path(config['info_dict']['reppro_dir'])

#script: Extract Light Curves for Deflaring
script = open(os.path.join(script_dir, 'deflare_point_sources.sh'), 'w')
script.write(f'cd {reppro_dir}\n')

for folder in os.listdir(reppro_dir):
    # folder is a string from os.listdir(); use it as the output root as well.
    obs_id =os.path.basename(folder.rstrip("/"))
    script.write(f'cd {folder}\n')
    script.write(f'pwd \n')

    bpix =os.popen(f'ls {reppro_dir}/{folder}/*repro_bpix1*').read().strip()

    script.write(f'punlearn ardlib \nacis_set_ardlib {bpix} \n')
    script.write(
        f'punlearn fluximage\n'
        f'fluximage ./ ./{obs_id} binsize=1 bands=0.5:7:2.3 clobber=yes\n'
    )

    script.write(
        f'punlearn mkpsfmap\n'
        f'mkpsfmap ./{obs_id}_0.5-7_thresh.img outfile=./{obs_id}_0.5-7.psf energy=2.3 ecf=0.9 clobber=yes\n'

    )



    script.write(
        f"""punlearn wavdetect
wavdetect infile=./{obs_id}_0.5-7_thresh.img \
psffile=./{obs_id}_0.5-7.psf \
expfile=./{obs_id}_0.5-7_thresh.expmap \
outfile=./{obs_id}_src_0.5-7.fits \
scellfile=./{obs_id}_scell_0.5-7.fits \
imagefile=./{obs_id}_imgfile_0.5-7.img \
defnbkgfile=./{obs_id}_defnbkg_0.5-7.fits \
regfile=./{obs_id}_src_0.5-7-noem.reg \
scales="1 2 4 8 16 32" \
maxiter=3 \
sigthresh=5e-6 \
ellsigma=5.0 \
clobber=yes\n
"""
    )

    script.write(f'echo "Region made for {obs_id} Make sure to check all the reg files, they might have taken some of the cluster too. So check the files manually and edit them if needed" \n')  
      
    script.write(f'echo "Make GTI file for {obs_id}"\n')

    script.write(f'ls -la *.reg \n')

    script.write(
f"""
punlearn dmcopy 
dmcopy "acisf{obs_id}_repro_evt2.fits[exclude sky=region({obs_id}_src_0.5-7-noem.reg)]" \
./{obs_id}_nosources.evt option=all clobber=yes
"""
    )

    script.write(
f"""
punlearn dmcopy
dmcopy "./{obs_id}_nosources.evt[energy=500:7000]" ./{obs_id}_0.5-7_nosources.evt option=all clobber=yes
"""
    )

    script.write(
f"""
punlearn dmextract
dmextract "./{obs_id}_0.5-7_nosources.evt[bin time=::259.28]" ./{obs_id}_0.5-7.lc opt=ltc1 clobber=yes
"""
    )

    script.write(
f"""
punlearn deflare
deflare ./{obs_id}_0.5-7.lc ./{obs_id}_0.5-7.gti method=clean
"""
    )

    script.write(
f"""
punlearn dmcopy
dmcopy "./acisf{obs_id}_repro_evt2.fits[@./{obs_id}_0.5-7.gti]" ./acisf{obs_id}_clean_evt.fits opt=all clobber=yes
"""
    )

    script.write(
f"""
echo "Make GTI file for {obs_id}" \n
"""
    )

    if get_obs_mode(obs_id) == 'VFAINT':
        script.write(
            f"""punlearn blanksky
blanksky evtfile="./acisf{obs_id}_repro_evt2.fits[@./{obs_id}_0.5-7.gti]" outfile=./{obs_id}_vfbackground_clean.evt tmpdir=./ clobber=yes
punlearn dmcopy
dmcopy "./{obs_id}_vfbackground_clean.evt[status=0]" ./{obs_id}_background_clean.evt clobber=yes
"""
            )
    else:
        script.write(
            f"""punlearn blanksky
blanksky evtfile="./acisf{obs_id}_repro_evt2.fits[@./{obs_id}_0.5-7.gti]" outfile=./{obs_id}_background_clean.evt tmpdir=./ clobber=yes
"""
        )
    
    script.write(
        f"""
dmhedit infile="./{obs_id}_background_clean.evt" filelist=none key="OBS_ID" value="{obs_id}" operation="add"
"""
    )

    script.write(
        f"""
blanksky_image bkgfile=./{obs_id}_background_clean.evt outroot=./{obs_id}_blank imgfile=./{obs_id}_0.5-7_thresh.img tmpdir=./ clobber=yes
"""
    )

    script.write(f'cd ../\n')


    script.write("#-----------------------------------------------------------\n")

script.write(f'python3 {reppro_dir}/update_flag.py flare_filtered\n')

print(f"Script created successfully: {script.name}")
script.close()
