from helpers import REPO_DIR
from astropy.io import fits
import numpy as np
import os

def _mkmap(input, output, head):
    fits.writeto(output, input, head, overwrite=True)

fluxim =fits.open(os.path.join(REPO_DIR, 'parent/Ophiuchus/merge_Ophiuchus_100.0_70/broad_flux.fits'))
fluxhdr = fluxim[0].header
fluximdata = fluxim[0].data


threshim = fits.open(os.path.join(REPO_DIR, 'parent/Ophiuchus/merge_Ophiuchus_100.0_70/broad_thresh.fits'))
threshimdata = threshim[0].data
expoim = fits.open(os.path.join(REPO_DIR, 'parent/Ophiuchus/merge_Ophiuchus_100.0_70/broad_thresh.expmap'))
expohd = expoim[0].header
expoimdata = expoim[0].data

threshsum = np.sum(threshimdata)
fluxsum = np.sum(fluximdata)
threshav = threshsum/ len(threshimdata)

fluxav = fluxsum/len(fluximdata)
scaledflux = (2.5*fluximdata*(threshav/fluxav))

_mkmap(scaledflux, os.path.join(REPO_DIR, 'parent/Ophiuchus/merge_Ophiuchus_100.0_70/scaled_broad_flux.fits'), fluxhdr)