from astropy.io import fits
from astropy.wcs import WCS
from regions import Regions
from astropy.coordinates import SkyCoord
import astropy.units as u
import os
from helpers import load_config, abs_path

config = load_config()

def convert_regions_to_wcs_sex(
    fitsfile,
    inputdir,
    outputdir,
    regnum
):
    os.makedirs(outputdir, exist_ok=True)

    # Load WCS
    with fits.open(fitsfile) as hdul:
        wcs = WCS(hdul[0].header)

    for i in range(regnum):
        infile = os.path.join(inputdir, f"xaf_{i}.reg")
        outfile = os.path.join(outputdir, f"xaf_{i}_sex.reg")

        regions = Regions.read(infile, format="ciao")

        out_regions = []
        for reg in regions:
            sky_reg = reg.to_sky(wcs)

            # force sexagesimal output
            if hasattr(sky_reg, "center"):
                sky_reg.center = SkyCoord(
                    ra=sky_reg.center.ra.to_string(unit=u.hour, sep=":"),
                    dec=sky_reg.center.dec.to_string(unit=u.deg, sep=":"),
                    frame="icrs"
                )

            out_regions.append(sky_reg)

        Regions(out_regions).write(outfile, format="ds9", overwrite=True)


convert_regions_to_wcs_sex(
    fitsfile=os.path.join(abs_path(config['info_dict']['map_file_dir']), "scaled_broad_flux_final.fits"),
    inputdir=os.path.join(abs_path(config['info_dict']['region_file_dir']), "outreg"),
    outputdir=os.path.join(abs_path(config['info_dict']['region_file_dir']), "sex_outreg"),
    regnum=10
)
