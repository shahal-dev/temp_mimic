# Chandra X-ray Data Processing Pipeline

## Complete Technical Reference

This document provides comprehensive documentation for processing Chandra X-ray Observatory ACIS data for spatially-resolved spectroscopy of galaxy clusters.

---

## Table of Contents

1. [Physical Background](#physical-background)
2. [Step 1: Configuration](#step-1-configuration)
3. [Step 2: Data Reprocessing](#step-2-data-reprocessing)
4. [Step 3: Deflaring and Point Source Detection](#step-3-deflaring-and-point-source-detection)
5. [Step 4: Merge Observations](#step-4-merge-observations)
6. [Step 5: Flux Map Creation](#step-5-flux-map-creation)
7. [Step 6: Crop and Remove Point Sources](#step-6-crop-and-remove-point-sources)
8. [Step 7: Contour Binning](#step-7-contour-binning)
9. [Step 8: Region Coordinate Conversion](#step-8-region-coordinate-conversion)
10. [Complete File Reference](#complete-file-reference)
11. [Physical Quantities Reference](#physical-quantities-reference)

---

## Physical Background

### Why X-ray Observations of Galaxy Clusters?

Galaxy clusters are the largest gravitationally bound structures in the universe. They contain:

1. **Galaxies** (~5% of mass) - visible in optical
2. **Dark Matter** (~80% of mass) - inferred from gravitational lensing
3. **Intracluster Medium (ICM)** (~15% of mass) - hot gas at T ~ 10⁷-10⁸ K

The ICM emits X-rays through **thermal bremsstrahlung** (free-free emission):

$$
\epsilon_{ff} \propto n_e^2 T^{1/2} \exp\left(-\frac{h\nu}{kT}\right)
$$

Where:
- $n_e$ = electron density (typically 10⁻³ - 10⁻¹ cm⁻³)
- $T$ = temperature (typically 2-15 keV, where 1 keV ≈ 1.16 × 10⁷ K)
- $h\nu$ = photon energy

### What We Measure

| Observable | Physical Information | How We Get It |
|------------|---------------------|---------------|
| X-ray surface brightness | $\int n_e^2 \, dl$ (emission measure) | Imaging |
| Spectrum shape | Temperature $T$ | Spectral fitting |
| Line ratios | Metal abundance $Z$ | Spectral fitting |
| Spatial temperature map | ICM thermodynamics | Spatially-resolved spectroscopy |

### The Goal of This Pipeline

Create **spatial regions** where we can extract spectra with sufficient signal-to-noise (S/N) to measure temperature and metallicity, while **preserving the physical structure** of the cluster (shocks, cold fronts, cavities).

---

## Step 1: Configuration

**File:** `step1_config.py`  
**Purpose:** Initialize pipeline parameters and directory structure

### Configuration Parameters

#### `name` (string)
- **What it is:** Identifier for the galaxy cluster
- **Example:** `"ophiuchus"`, `"perseus"`, `"abell2029"`
- **Physical meaning:** The astronomical target name, used for directory naming
- **Where it's used:** All subsequent scripts for file paths

#### `sn_per_region` (integer)
- **What it is:** Target signal-to-noise ratio per spectral extraction region
- **Example:** `70`
- **Physical meaning:** Determines the precision of temperature/metallicity measurements
- **Trade-off:** 
  - Higher S/N → more precise temperatures, but fewer/larger spatial bins
  - Lower S/N → more spatial resolution, but larger temperature uncertainties

**Relationship to temperature uncertainty:**
$$
\frac{\Delta T}{T} \approx \frac{1}{\text{S/N}} \times f(T, N_H, Z)
$$

For S/N = 70, typical temperature uncertainty is ~5-10%.

**Minimum counts needed:**
$$
N_{\text{counts}} \approx (\text{S/N})^2 = 70^2 = 4900 \text{ counts per region}
$$

#### `reg_smoothness` (float)
- **What it is:** Signal-to-noise for the smoothed image used to define contours
- **Example:** `100.0`
- **Physical meaning:** Controls how smooth the bin boundaries are
- **Trade-off:**
  - Higher value → smoother contours, bins follow large-scale structure
  - Lower value → more irregular bins, may follow noise features

**Recommendation:** Set `smoothsn` > `sn` to ensure contours are well-defined.

#### `cluster_directory` (path)
- **What it is:** Location of raw Chandra data downloaded from archive
- **Physical contents:** Primary and secondary data products from CXC
- **Structure:**
```
cluster_directory/
├── {obs_id1}/
│   ├── primary/
│   │   └── acisf{obs_id}_evt2.fits.gz   # Level 2 event file
│   └── secondary/
│       ├── *asol*.fits                   # Aspect solution
│       ├── *bpix*.fits                   # Bad pixel file
│       └── ...
├── {obs_id2}/
...
```

### Output: `config.json`

```json
{
    "info_dict": {
        "name": "ophiuchus",
        "sn_per_region": 70,
        "reg_smoothness": 100.0,
        "cluster_directory": "data",
        "obs_ids": ["16626", "16143", "16464", "16142", "16627"]
    },
    "flags": {
        "reprocessed": false,
        "flare_filtered": false,
        ...
    }
}
```

### Processing Flags

| Flag | Set True When | Physical Meaning |
|------|--------------|------------------|
| `reprocessed` | Step 2 complete | Data has latest calibration applied |
| `flare_filtered` | Step 3 complete | Background flares removed, clean GTI created |
| `merge_data` | Step 4 complete | Multiple observations combined |
| `flux_maps` | Step 5 complete | Exposure-corrected flux image ready |
| `remove_point_source` | Step 6 complete | AGN/stars masked, ready for binning |
| `contour_binning` | Step 7 complete | Spectral extraction regions defined |
| `convert_region_coordinates` | Step 8 complete | Regions in WCS coordinates |

---

## Step 2: Data Reprocessing

**File:** `step2_repro.py`  
**Output Script:** `preprocess_data.sh`  
**Purpose:** Apply latest calibration to raw event data

### Why Reprocess?

Raw Chandra data uses calibration files from when the data was processed at CXC. Reprocessing applies:

1. **Updated gain maps** - Convert PHA (pulse height) to PI (energy) more accurately
2. **CTI corrections** - Charge Transfer Inefficiency degrades over mission lifetime
3. **Bad pixel updates** - New hot pixels identified since original processing
4. **Improved ACIS background screening**

### CIAO Tool: `chandra_repro`

```bash
chandra_repro {obs_id} [check_vf_pha=yes] outdir={output_dir} verbose=1 clobber=yes
```

#### Parameters Explained

| Parameter | Value | Physical Meaning |
|-----------|-------|------------------|
| `{obs_id}` | e.g., `16626` | Chandra observation identifier (unique per pointing) |
| `check_vf_pha` | `yes` | Enable VFAINT background screening (if data supports it) |
| `outdir` | path | Where to write reprocessed files |
| `verbose` | `1` | Print processing information |
| `clobber` | `yes` | Overwrite existing files |

#### `check_vf_pha=yes` - VFAINT Mode Screening

**Physical Background:**

ACIS CCDs detect X-rays when photons create electron-hole pairs in silicon. But cosmic rays (high-energy particles) also create charge, contaminating the data.

**FAINT mode:** Records 3×3 pixel event island
**VFAINT mode:** Records 5×5 pixel event island

The outer ring of the 5×5 island should have zero charge for a real X-ray (which deposits all energy in ~1 pixel). Cosmic rays create charge trails across multiple pixels.

**Screening criterion:**
$$
\sum_{i \in \text{outer 16 pixels}} \text{PHA}_i < \text{threshold}
$$

Events failing this test are flagged with `status ≠ 0` and can be filtered out.

**Impact:** Reduces particle background by ~20-30% for observations in VFAINT mode.

### Output Files

| File | Contents | Physical Meaning |
|------|----------|------------------|
| `acisf{obs_id}_repro_evt2.fits` | Event list | Each row = one detected X-ray photon with time, position (x,y), energy (PI), grade |
| `acisf{obs_id}_repro_bpix1.fits` | Bad pixel map | Pixels to exclude (hot, dead, flickering) |
| `*_asol1.fits` | Aspect solution | Spacecraft pointing vs time (for dither correction) |

### Event File Structure

Each event (photon) has these key columns:

| Column | Units | Physical Meaning |
|--------|-------|------------------|
| `TIME` | seconds | Mission elapsed time since 1998-01-01 |
| `X`, `Y` | sky pixels | Position in tangent-plane projection (0.492"/pixel) |
| `PI` | channel | Energy channel (1 channel ≈ 14.6 eV) |
| `ENERGY` | eV | Calibrated photon energy |
| `CCD_ID` | 0-9 | Which ACIS chip detected the event |
| `GRADE` | 0-255 | Event morphology (used for screening) |
| `STATUS` | bits | Quality flags (0 = good) |

---

## Step 3: Deflaring and Point Source Detection

**File:** `step3_primary_deflare.py`  
**Output Script:** `deflare_point_sources.sh`  
**Purpose:** Remove background contamination and detect/mask point sources

### Physical Context

**Background flares:** Solar protons interacting with the detector create sudden increases in count rate. These are NOT X-rays from the target and must be removed.

**Point sources:** Active Galactic Nuclei (AGN), X-ray binaries, and foreground stars appear as point-like sources superimposed on the diffuse cluster emission. They have different spectra and must be masked.

---

### CIAO Tool: `fluximage`

```bash
fluximage ./ ./{obs_id} binsize=1 bands=0.5:7:2.3 clobber=yes
```

#### Parameters Explained

| Parameter | Value | Physical Meaning |
|-----------|-------|------------------|
| `binsize` | `1` | Output pixel size = 1 native ACIS pixel = 0.492 arcsec |
| `bands` | `0.5:7:2.3` | Energy range 0.5-7 keV, effective energy 2.3 keV |

#### `bands=0.5:7:2.3` Breakdown

Format: `Emin:Emax:Eeff`

| Component | Value | Physical Meaning |
|-----------|-------|------------------|
| `Emin` | 0.5 keV | Low energy cutoff (below this: high background, poor calibration) |
| `Emax` | 7.0 keV | High energy cutoff (above this: low effective area, high background) |
| `Eeff` | 2.3 keV | Effective energy for computing exposure map |

**Why 0.5-7 keV?**

- **Below 0.5 keV:** High background from soft protons, absorption by Galactic H I column
- **0.5-2 keV:** Soft band, sensitive to cool gas (T < 3 keV)
- **2-7 keV:** Hard band, sensitive to hot gas (T > 3 keV)
- **Above 7 keV:** Chandra effective area drops, particle background dominates

**Why Eeff = 2.3 keV?**

The exposure map depends on energy (through effective area and vignetting). 2.3 keV is a good "average" for the broad band, representing where most cluster photons are detected.

#### Output Files

| File | Contents | Physical Meaning |
|------|----------|------------------|
| `{obs_id}_0.5-7_thresh.img` | Counts image | Raw photon counts per pixel in 0.5-7 keV |
| `{obs_id}_0.5-7_thresh.expmap` | Exposure map | Effective exposure time × area per pixel [cm² s] |
| `{obs_id}_0.5-7_flux.img` | Flux image | counts / exposure [photons/cm²/s] |

#### Exposure Map Physics

The exposure map accounts for:

$$
E(x,y) = t_{\text{live}} \times A_{\text{eff}}(E, \theta) \times V(\theta) \times D(x,y)
$$

| Component | Symbol | Physical Meaning |
|-----------|--------|------------------|
| Live time | $t_{\text{live}}$ | Total exposure minus dead time, GTI gaps |
| Effective area | $A_{\text{eff}}$ | Mirror collecting area × CCD quantum efficiency |
| Vignetting | $V(\theta)$ | Reduction of effective area off-axis |
| Dither correction | $D(x,y)$ | Accounts for spacecraft wobble during exposure |

**Vignetting function:**
$$
V(\theta) \approx 1 - 0.1 \times \left(\frac{\theta}{10'}\right)^2
$$

At 10 arcmin off-axis, effective area is reduced by ~10%.

---

### CIAO Tool: `mkpsfmap`

```bash
mkpsfmap {obs_id}_0.5-7_thresh.img outfile={obs_id}_0.5-7.psf energy=2.3 ecf=0.9 clobber=yes
```

#### Parameters Explained

| Parameter | Value | Physical Meaning |
|-----------|-------|------------------|
| `energy` | `2.3` keV | Energy at which to compute PSF size |
| `ecf` | `0.9` | Encircled Counts Fraction = 90% |

#### PSF Physics

The Chandra PSF is the sharpest of any X-ray telescope but degrades off-axis:

**On-axis (θ = 0):**
- FWHM ≈ 0.5 arcsec (sub-arcsecond resolution!)
- 90% ECF radius ≈ 1 arcsec

**Off-axis:**
$$
r_{90\%}(\theta) \approx 1'' \times \sqrt{1 + \left(\frac{\theta}{3'}\right)^4}
$$

At 5 arcmin off-axis: PSF 90% radius ≈ 5 arcsec
At 10 arcmin off-axis: PSF 90% radius ≈ 20 arcsec

#### `ecf=0.9` Meaning

The PSF map stores the radius containing 90% of a point source's counts at each position. This is used by wavdetect to set appropriate source detection cell sizes.

**Why 90%?**
- Too small (e.g., 50%): Misses extended wings of off-axis sources
- Too large (e.g., 99%): Source cells overlap too much, reducing sensitivity

---

### CIAO Tool: `wavdetect`

```bash
wavdetect infile={obs_id}_0.5-7_thresh.img \
  psffile={obs_id}_0.5-7.psf \
  expfile={obs_id}_0.5-7_thresh.expmap \
  outfile={obs_id}_src_0.5-7.fits \
  scellfile={obs_id}_scell_0.5-7.fits \
  imagefile={obs_id}_imgfile_0.5-7.img \
  defnbkgfile={obs_id}_defnbkg_0.5-7.fits \
  regfile={obs_id}_src_0.5-7-noem.reg \
  scales="1 2 4 8 16 32" \
  maxiter=3 \
  sigthresh=5e-6 \
  ellsigma=5.0 \
  clobber=yes
```

#### Parameters Explained

| Parameter | Value | Physical Meaning |
|-----------|-------|------------------|
| `scales` | `"1 2 4 8 16 32"` | Wavelet scales in pixels (0.5" to 16") |
| `maxiter` | `3` | Number of iterations for source subtraction |
| `sigthresh` | `5e-6` | False positive probability threshold |
| `ellsigma` | `5.0` | Source ellipse size in sigma units |

#### `scales="1 2 4 8 16 32"` - Wavelet Scales

Each scale is sensitive to sources of different angular sizes:

| Scale (pixels) | Angular Size | Sensitive To |
|----------------|--------------|--------------|
| 1 | 0.5" | On-axis point sources |
| 2 | 1" | Slightly extended or off-axis point sources |
| 4 | 2" | Moderately extended sources |
| 8 | 4" | Extended sources (e.g., nearby galaxy nuclei) |
| 16 | 8" | Large extended sources |
| 32 | 16" | Very extended structures |

**Mexican Hat wavelet at scale s:**
$$
\psi_s(r) = \left(1 - \frac{r^2}{s^2}\right) \exp\left(-\frac{r^2}{2s^2}\right)
$$

This wavelet is **positive** in the center and **negative** in the annulus, making it optimal for detecting localized excesses above a local background.

#### `sigthresh=5e-6` - Detection Threshold

**Physical meaning:** Probability of a false detection per pixel per scale.

For an image with N pixels and S scales:
$$
N_{\text{false}} \approx N \times S \times \text{sigthresh}
$$

For a 4096×4096 image with 6 scales:
$$
N_{\text{false}} \approx 16.8 \times 10^6 \times 6 \times 5 \times 10^{-6} \approx 0.5 \text{ false sources}
$$

**Equivalent significance:**
$$
\text{sigthresh} = 5 \times 10^{-6} \Leftrightarrow 4.4\sigma \text{ (one-sided)}
$$

#### `ellsigma=5.0` - Source Region Size

Detected sources are characterized by ellipses. `ellsigma=5.0` means the ellipse semi-axes are 5× the fitted Gaussian sigma:

$$
a = 5 \sigma_{\text{major}}, \quad b = 5 \sigma_{\text{minor}}
$$

For a Gaussian, 5σ contains 99.99994% of the flux. This ensures essentially all source counts are included in the region.

#### Output Files

| File | Contents | Use |
|------|----------|-----|
| `{obs_id}_src_0.5-7.fits` | Source catalog | Table of detected sources with positions, counts, significance |
| `{obs_id}_src_0.5-7-noem.reg` | Region file | DS9/CIAO regions for masking |
| `{obs_id}_scell_0.5-7.fits` | Source cell image | Which scale detected each pixel |
| `{obs_id}_defnbkg_0.5-7.fits` | Background image | Local background estimate |

---

### CIAO Tool: `dmcopy` (Point Source Removal)

```bash
dmcopy "acisf{obs_id}_repro_evt2.fits[exclude sky=region({obs_id}_src_0.5-7-noem.reg)]" \
  {obs_id}_nosources.evt option=all clobber=yes
```

#### Filter Syntax

`[exclude sky=region(file.reg)]` removes all events within the regions defined in the file.

**Physical effect:** Creates an event file where pixels inside point source ellipses have zero counts. This is necessary for:
1. Accurate light curves (point source variability would contaminate deflaring)
2. Clean diffuse emission analysis

---

### CIAO Tool: `dmextract` (Light Curve)

```bash
dmextract "{obs_id}_0.5-7_nosources.evt[bin time=::259.28]" {obs_id}_0.5-7.lc opt=ltc1 clobber=yes
```

#### Parameters Explained

| Parameter | Value | Physical Meaning |
|-----------|-------|------------------|
| `bin time=::259.28` | 259.28 s | Time bin size for light curve |
| `opt=ltc1` | - | Light curve output format |

#### `bin time=::259.28` - Why This Value?

**ACIS frame time:** 3.24104 seconds (time to read out one CCD frame)

**Bin size:** 259.28 s = 80 × 3.24104 s = 80 frames

**Physical reasoning:**
- Too short bins: Dominated by Poisson noise, can't detect real flares
- Too long bins: Flares get averaged out, reducing sensitivity
- 80 frames provides good sensitivity to flares lasting 5-10 minutes

#### Output: Light Curve File

| Column | Units | Physical Meaning |
|--------|-------|------------------|
| `TIME` | s | Center of time bin |
| `COUNT_RATE` | cts/s | Background count rate in this interval |
| `COUNT_RATE_ERR` | cts/s | Poisson uncertainty = √N / Δt |

---

### CIAO Tool: `deflare`

```bash
deflare {obs_id}_0.5-7.lc {obs_id}_0.5-7.gti method=clean
```

#### Parameters Explained

| Parameter | Value | Physical Meaning |
|-----------|-------|------------------|
| `method` | `clean` | Iterative sigma-clipping algorithm |

#### Algorithm: `method=clean`

1. Compute mean count rate $\bar{r}$ and standard deviation $\sigma$
2. Identify outliers: time bins where $|r_i - \bar{r}| > 3\sigma$
3. Remove outliers from sample
4. Repeat until no more outliers found (convergence)
5. Good Time Intervals = time bins that were never flagged

**Physical interpretation:**

Quiescent background has a characteristic count rate set by:
- Cosmic X-ray background
- Instrumental background (particle-induced)
- Diffuse cluster emission

Flares (from solar protons hitting the detector) cause sudden increases of 2-100× the quiescent rate.

#### Output: Good Time Interval (GTI) File

The GTI file contains:

| Column | Units | Meaning |
|--------|-------|---------|
| `START` | s | Start of good interval |
| `STOP` | s | End of good interval |

**Typical result:** 5-20% of exposure may be lost to flares, depending on solar activity.

---

### CIAO Tool: `blanksky`

```bash
blanksky evtfile="acisf{obs_id}_repro_evt2.fits[@{obs_id}_0.5-7.gti]" \
  outfile={obs_id}_background_clean.evt tmpdir=./ clobber=yes
```

#### What is Blank-Sky Background?

The Chandra calibration database (CALDB) contains "blank-sky" observations—long exposures of regions with no bright sources. These provide a template for the instrumental + cosmic background.

#### How `blanksky` Works

1. **Select matching dataset:** Finds blank-sky file for same ACIS configuration, similar epoch
2. **Reproject:** Rotates blank-sky events to match observation roll angle
3. **Filter:** Applies same energy range and chip selection
4. **Normalize:** Scales to match observation's 9-12 keV count rate (where cluster emission is negligible)

#### VFAINT Background Processing

```bash
blanksky evtfile="..." outfile={obs_id}_vfbackground_clean.evt ...
dmcopy "{obs_id}_vfbackground_clean.evt[status=0]" {obs_id}_background_clean.evt
```

The `[status=0]` filter removes events that failed VFAINT screening, giving cleaner background for VFAINT observations.

#### Output File Usage

The background event file is used later for:
1. Background subtraction in spectral fitting
2. Creating background images for imaging analysis
3. Estimating systematic uncertainties

---

### CIAO Tool: `blanksky_image`

```bash
blanksky_image bkgfile={obs_id}_background_clean.evt outroot={obs_id}_blank \
  imgfile={obs_id}_0.5-7_thresh.img tmpdir=./ clobber=yes
```

Creates a background **image** (not event list) matched to the observation's image binning and exposure.

---

## Step 4: Merge Observations

**File:** `step4_merge_data.py`  
**Output Script:** `merge_data.sh`  
**Purpose:** Combine multiple observations for deeper imaging

### Why Merge?

Single Chandra observations are typically 20-100 ks (5-28 hours). For detailed cluster analysis, we often need 200-500 ks total exposure, requiring multiple observations.

**Benefits of merging:**
- Increased S/N: $\text{S/N} \propto \sqrt{t_{\text{exposure}}}$
- Better coverage of chip gaps (different roll angles)
- Redundancy for systematic checks

---

### Input: `clean_evt.list`

```
/path/to/acisf16626_clean_evt.fits[ccd_id=0:3]
/path/to/acisf16143_clean_evt.fits[ccd_id=0:3]
...
```

#### CCD Filter: `[ccd_id=0:3]` vs `[ccd_id=4:9]`

| Array | CCD IDs | Physical Description |
|-------|---------|---------------------|
| ACIS-I | 0, 1, 2, 3 | Imaging array, 4 front-illuminated CCDs in 2×2 |
| ACIS-S | 4, 5, 6, 7, 8, 9 | Spectroscopy array, 6 CCDs in 1×6 |

**Why filter by CCD?**

- ACIS-I and ACIS-S have different backgrounds, responses
- Chip gaps create artifacts if both arrays merged
- Most cluster observations use ACIS-I (larger FOV)

The pipeline automatically detects which array was primarily used via the `DETNAM` header keyword.

---

### CIAO Tool: `merge_obs`

```bash
merge_obs @clean_evt.list {merge_dir}/ bin=1 bands=broad clobber=yes
```

#### Parameters Explained

| Parameter | Value | Physical Meaning |
|-----------|-------|------------------|
| `@clean_evt.list` | file | List of event files to merge (@ = read from file) |
| `bin` | `1` | Output pixel size = 1 ACIS pixel = 0.492" |
| `bands` | `broad` | Predefined band: 0.5-7 keV |

#### `bin=1` - Pixel Size Choice

| Bin Value | Pixel Size | Use Case |
|-----------|------------|----------|
| 1 | 0.492" | Full resolution, best for point sources |
| 2 | 0.984" | Reduced resolution, smaller files |
| 4 | 1.968" | For very extended, low surface brightness |

**For cluster work:** `bin=1` preserves maximum spatial information for contour binning.

#### `bands=broad` - Energy Band

Predefined bands in CIAO:

| Band | Energy Range | Physical Meaning |
|------|--------------|------------------|
| `broad` | 0.5-7.0 keV | Full useful ACIS range |
| `soft` | 0.5-1.2 keV | Cool gas, strong absorption effects |
| `medium` | 1.2-2.0 keV | Intermediate |
| `hard` | 2.0-7.0 keV | Hot gas, less absorption |
| `ultrahard` | 4.0-8.0 keV | Very hot gas, AGN |

#### Reprojection Process

Each observation has a different:
- **Aim point:** Center of FOV on sky
- **Roll angle:** Rotation of detector on sky

`merge_obs` reprojects all events to a common **tangent point** (usually the first observation's aim point) using the WCS transformation:

$$
\begin{pmatrix} x' \\ y' \end{pmatrix} = \mathbf{R}(\theta) \cdot \begin{pmatrix} x - x_0 \\ y - y_0 \end{pmatrix} + \begin{pmatrix} x'_0 \\ y'_0 \end{pmatrix}
$$

Where $\mathbf{R}(\theta)$ is a rotation matrix for the roll angle difference.

#### Output Files

| File | Contents | Physical Meaning |
|------|----------|------------------|
| `merged_evt.fits` | Combined event list | All photons from all observations |
| `broad_thresh.img` | Merged counts image | Total counts per pixel |
| `broad_flux.img` | Merged flux image | Exposure-corrected surface brightness |
| `broad_thresh.expmap` | Merged exposure map | Combined effective exposure [cm² s] |
| `merged.fov` | Field of view region | Outline of combined coverage |

#### Exposure Map Combination

For overlapping regions:
$$
E_{\text{merged}}(x,y) = \sum_{i=1}^{N_{\text{obs}}} E_i(x,y)
$$

The merged flux image is:
$$
F_{\text{merged}}(x,y) = \frac{\sum_i C_i(x,y)}{\sum_i E_i(x,y)}
$$

---

## Step 5: Flux Map Creation

**File:** `step5_merge_data_flux.py`  
**Purpose:** Create scaled flux image optimized for contour binning

### The Scaling Problem

Contour binning needs an image where pixel values represent **signal** for S/N calculation. The raw flux image has issues:

1. **Units:** photons/cm²/s—not directly counts
2. **Background:** Not subtracted
3. **Scaling:** May have very small values that cause numerical issues

### Algorithm

```python
scaledflux = 2.5 * fluximdata * (threshav / fluxav)
```

#### Mathematical Breakdown

$$
F_{\text{scaled}}(x,y) = 2.5 \times F(x,y) \times \frac{\bar{C}}{\bar{F}}
$$

Where:
- $F(x,y)$ = flux image value [photons/cm²/s]
- $\bar{C}$ = mean counts per pixel
- $\bar{F}$ = mean flux per pixel
- 2.5 = empirical scaling factor

#### Physical Interpretation

| Term | What It Does |
|------|--------------|
| $F(x,y)$ | Preserves spatial structure |
| $\bar{C}/\bar{F}$ | Converts flux back to count-like units |
| 2.5 | Empirical factor to optimize S/N estimation in contbin |

The result: pixel values are proportional to expected counts, suitable for S/N calculation:
$$
\text{S/N} \approx \sqrt{F_{\text{scaled}}}
$$

### Output File

| File | Contents | Use |
|------|----------|-----|
| `scaled_broad_flux.fits` | Scaled flux image | Input for contour binning |

---

## Step 6: Crop and Remove Point Sources

**File:** `step6_crop_and_nopointsource.py`  
**Output Script:** `crop_data.sh`  
**Purpose:** Clean the image for contour binning

### Manual Region Files Required

These must be created manually in DS9:

#### `src_0.5-7-nps-noem.reg` (Cluster Emission Region)

**Purpose:** Define the extended cluster emission to exclude for point source detection.

**Why needed:** The cluster itself is a bright extended source. If not masked, wavdetect would either:
- Detect the cluster core as a "source"
- Have elevated background, missing faint point sources

**How to create:**
1. Open `broad_thresh.img` in DS9
2. Draw a large circle/ellipse encompassing all visible cluster emission
3. Save as CIAO format, WCS coordinates

#### `broad_src_0.5-7-pointsources.reg` (Point Sources)

**Purpose:** Mark point sources detected by wavdetect that should be removed.

**How to create:**
1. Run wavdetect on cluster-masked image
2. Review detected sources—remove any that are part of the cluster
3. Add any obvious point sources wavdetect missed

#### `square.reg` (Region of Interest)

**Purpose:** Define the analysis area, excluding edges with poor exposure.

**How to create:**
1. Draw a box/polygon around the region you want to analyze
2. Exclude areas near chip edges, chip gaps, bad columns

#### `min_xy.reg` (Physical Coordinates)

**Same region as `square.reg`**, but saved in **physical pixel coordinates** instead of WCS. Needed for `make_region_files` which requires pixel coordinates.

### Processing Steps

#### Step 6.1: Remove Cluster Emission

```bash
dmcopy "broad_thresh.img[exclude sky=region(src_0.5-7-nps-noem.reg)]" broad_thresh_noem.img
```

Creates an image with the cluster masked out, used for detecting point sources in the field.

#### Step 6.2: Detect Point Sources in Merged Image

```bash
wavdetect infile=broad_thresh_noem.img \
  psffile=none \
  expfile=broad_thresh.expmap \
  ...
```

**Note:** `psffile=none` because the merged image has variable PSF across the field (different observations have different roll angles). Wavdetect uses default PSF assumptions.

#### Step 6.3: Remove Point Sources from Flux Image

```bash
dmcopy "scaled_broad_flux.fits[exclude sky=region(broad_src_0.5-7.reg)]" \
  scaled_broad_flux_cropped.fits
```

Point sources are now masked (pixel values set to NaN or 0).

#### Step 6.4: Crop to Region of Interest

```bash
dmcopy "scaled_broad_flux_cropped.fits[sky=region(square.reg)]" \
  scaled_broad_flux_final.fits
```

**Note:** `[sky=region(...)]` (without "exclude") **includes** only pixels inside the region.

### Output Files

| File | Contents | Next Step |
|------|----------|-----------|
| `broad_thresh_noem.img` | Counts with cluster masked | Point source detection |
| `broad_src_0.5-7.reg` | Detected point sources | Point source masking |
| `scaled_broad_flux_cropped.fits` | Flux with point sources removed | Cropping |
| `scaled_broad_flux_final.fits` | Final clean flux image | Contour binning |

---

## Step 7: Contour Binning

**File:** `step7_countour_bin.py`  
**Output Script:** `contour_binning.sh`  
**Purpose:** Create adaptive spatial bins following surface brightness contours

### Physical Motivation

Galaxy clusters have **temperature gradients** that generally follow **surface brightness contours**:

- Bright core → cooler (3-5 keV)
- Fainter outskirts → hotter (5-10 keV)
- Shocks/cold fronts → sharp temperature changes at brightness edges

**Traditional binning (e.g., Voronoi):** Creates roughly circular bins → mixes gas at different temperatures → biased temperature measurements.

**Contour binning:** Follows the natural structure → bins contain gas at similar temperatures → more accurate measurements.

---

### Tool: `contbin`

```bash
contbin --sn=70 --smoothsn=100.0 --constrainfill --constrainval=3. input.fits
```

#### Parameters Explained

| Parameter | Value | Physical Meaning |
|-----------|-------|------------------|
| `--sn` | `70` | Target S/N per bin |
| `--smoothsn` | `100.0` | S/N for contour-defining smoothed image |
| `--constrainfill` | flag | Enable shape constraints |
| `--constrainval` | `3.0` | Maximum length/width ratio |

#### `--sn=70` - Target Signal-to-Noise

**Physical meaning:** Each bin will have approximately S/N = 70, meaning:

$$
\frac{N_{\text{source}}}{\sqrt{N_{\text{source}} + N_{\text{background}}}} \approx 70
$$

**Implications for spectral fitting:**

| S/N | Temperature Uncertainty | Metallicity Uncertainty | Typical Bin Size |
|-----|------------------------|------------------------|------------------|
| 30 | ~20% | ~50% | Small (high resolution) |
| 50 | ~10% | ~30% | Medium |
| 70 | ~7% | ~20% | Large |
| 100 | ~5% | ~15% | Very large |

**Rule of thumb:** For cluster temperature maps, S/N ≥ 50 is typically needed.

#### `--smoothsn=100.0` - Smoothing S/N

**Physical meaning:** The image is smoothed to S/N = 100 before identifying contours.

**Why smooth?**
- Raw image has Poisson noise
- Noise causes jagged, meaningless contours
- Smoothing reveals the true brightness structure

**Relationship to `--sn`:**
- `smoothsn` should be > `sn` to ensure contours are well-defined
- Typical: `smoothsn` = 1.5-2 × `sn`

**Effect of smoothsn:**

| smoothsn | Contour Behavior | Best For |
|----------|-----------------|----------|
| Low (50) | Follows small-scale structure | Detecting fine features |
| Medium (100) | Balanced | General use |
| High (200) | Very smooth contours | Large-scale structure |

#### `--constrainfill` and `--constrainval=3.0`

**Physical meaning:** Prevents bins from becoming too elongated.

Without constraints, bins might stretch along contours into long, thin regions that:
- Are hard to interpret physically
- May cross temperature gradients perpendicular to contours
- Create messy region files

**`constrainval=3.0`** means: maximum aspect ratio = 3:1

If a bin would become more elongated, the algorithm starts a new bin.

---

### Algorithm (Sanders 2006)

1. **Smooth the image** to target S/N using adaptive Gaussian smoothing:
   $$\sigma_{\text{smooth}}(x,y) = \text{radius where } \text{S/N} = \text{smoothsn}$$

2. **Identify contours** of constant surface brightness in the smoothed image

3. **Seed bins** at local maxima (brightest pixels)

4. **Accrete pixels** to each bin:
   - Add neighboring pixels with similar smoothed brightness
   - Stop when S/N target reached
   - Respect shape constraints

5. **Iterate** until all pixels assigned or below threshold

---

### Tool: `make_region_files`

```bash
make_region_files --minx={min_x} --miny={min_y} --bin=1 --outdir=outreg contbin_binmap.fits
```

#### Parameters Explained

| Parameter | Value | Physical Meaning |
|-----------|-------|------------------|
| `--minx` | float | X-coordinate of image origin in physical pixels |
| `--miny` | float | Y-coordinate of image origin in physical pixels |
| `--bin` | `1` | Binning factor of input image |
| `--outdir` | `outreg` | Output directory for region files |

#### `--minx` and `--miny` - Coordinate Origin

**Why needed:** The binmap image has its own pixel coordinates starting at (0,0). But the original event file uses **physical sky coordinates** (typically centered around 4096.5, 4096.5).

The conversion:
$$
x_{\text{physical}} = x_{\text{binmap}} \times \text{bin} + \text{minx}
$$
$$
y_{\text{physical}} = y_{\text{binmap}} \times \text{bin} + \text{miny}
$$

**How to get these values:** From the FITS header keyword `DSVAL1` of the cropped image:

```
DSVAL1 = 'box(4500.5,4200.3,1000,800,0)'
```
→ center = (4500.5, 4200.3), size = (1000, 800)
→ minx = 4500.5 - 1000/2 = 4000.5
→ miny = 4200.3 - 800/2 = 3800.3

---

### Output Files

| File | Contents | Physical Meaning |
|------|----------|------------------|
| `contbin_binmap.fits` | Bin assignment image | Each pixel value = bin number (0, 1, 2, ...) |
| `contbin_sn.fits` | S/N map | Achieved S/N at each pixel |
| `contbin_out.fits` | Output data | Bin statistics |
| `contbin_mask.fits` | Valid pixel mask | 1 = included, 0 = excluded |
| `bin_sn_stats.qdp` | S/N statistics | Histogram of achieved S/N values |
| `outreg/xaf_0.reg` | Region for bin 0 | CIAO polygon region file |
| `outreg/xaf_1.reg` | Region for bin 1 | ... |
| ... | ... | One file per bin |

#### Region File Format (CIAO)

```
# Region file format: CIAO version 1.0
polygon(4523.5,4102.5,4524.5,4102.5,4524.5,4103.5,...)
```

These are **physical pixel coordinates** that can be used directly with `dmextract` for spectral extraction.

---

## Step 8: Region Coordinate Conversion

**File:** `step8_regCoordChange.py`  
**Output Script:** `regCoordChange.sh`  
**Purpose:** Convert region coordinates from physical pixels to WCS

### Why Convert?

| Coordinate System | Pros | Cons |
|-------------------|------|------|
| Physical pixels | Fast, simple | Tied to specific image/binning |
| WCS (RA/Dec) | Universal, portable | Slightly slower to process |

**For spectral extraction:** Physical coordinates are fine.

**For publication/sharing:** WCS coordinates are preferred.

**For multi-observation analysis:** WCS ensures regions match across different observations with different aim points.

---

### Method: DS9 + XPA

The script uses SAOImage DS9's XPA (X Public Access) protocol:

```bash
# Start virtual display (for headless servers)
Xvfb :1234 -screen 0 1024x768x24 &
DISPLAY=:1234 ds9 image.fits &

# For each region file:
xpaset -p ds9 regions load {input}.reg      # Load region
xpaset -p ds9 regions format ciao           # Input format
xpaset -p ds9 regions system wcs            # Convert to WCS
xpaset -p ds9 regions skyformat sexagesimal # Use hh:mm:ss format
xpaset -p ds9 regions save {output}.reg     # Save converted
xpaset -p ds9 regions delete all            # Clear for next
```

#### XPA Commands Explained

| Command | What It Does |
|---------|--------------|
| `regions load` | Load a region file into DS9 |
| `regions format ciao` | Interpret regions as CIAO format |
| `regions system wcs` | Convert coordinates to World Coordinate System |
| `regions skyformat sexagesimal` | Format RA as hh:mm:ss, Dec as dd:mm:ss |
| `regions save` | Write regions to file |

### Coordinate System Comparison

**Input (Physical):**
```
polygon(4523.5,4102.5,4524.5,4102.5,4524.5,4103.5,...)
```

**Output (WCS Sexagesimal):**
```
fk5;polygon(17:12:26.952,-23:22:31.08,17:12:26.901,-23:22:31.08,...)
```

### WCS Keywords in FITS Header

The conversion uses these FITS header keywords:

| Keyword | Meaning | Example |
|---------|---------|---------|
| `CRPIX1`, `CRPIX2` | Reference pixel | 4096.5, 4096.5 |
| `CRVAL1`, `CRVAL2` | Reference sky coordinate (deg) | 258.112, -23.375 |
| `CD1_1`, `CD1_2` | Transformation matrix row 1 | -0.000137, 0.0 |
| `CD2_1`, `CD2_2` | Transformation matrix row 2 | 0.0, 0.000137 |
| `CTYPE1`, `CTYPE2` | Projection type | RA---TAN, DEC--TAN |

**Transformation:**
$$
\begin{pmatrix} \Delta\alpha \cos\delta \\ \Delta\delta \end{pmatrix} = 
\begin{pmatrix} \text{CD1\_1} & \text{CD1\_2} \\ \text{CD2\_1} & \text{CD2\_2} \end{pmatrix}
\begin{pmatrix} x - \text{CRPIX1} \\ y - \text{CRPIX2} \end{pmatrix}
$$

Then:
$$
\alpha = \text{CRVAL1} + \Delta\alpha / \cos\delta
$$
$$
\delta = \text{CRVAL2} + \Delta\delta
$$

### Sexagesimal Format

**Right Ascension (RA):**
- Input: 258.112° (decimal degrees)
- Output: 17:12:26.88 (hours:minutes:seconds)
- Conversion: RA(hours) = RA(deg) / 15

**Declination (Dec):**
- Input: -23.375° (decimal degrees)
- Output: -23:22:30.0 (degrees:arcmin:arcsec)

---

## Complete File Reference

### Input Files (User Provided)

| File | Created In | Contents |
|------|------------|----------|
| Raw data from CXC | Downloaded | Level 1/2 event files, calibration |
| `src_0.5-7-nps-noem.reg` | Step 6 (manual) | Cluster emission boundary |
| `broad_src_0.5-7-pointsources.reg` | Step 6 (manual) | Point sources to mask |
| `square.reg` | Step 6 (manual) | Analysis region boundary (WCS) |
| `min_xy.reg` | Step 6 (manual) | Same boundary (physical coords) |

### Generated Files by Step

#### Step 2: Reprocessing

| File | Location | Contents |
|------|----------|----------|
| `acisf{obs}_repro_evt2.fits` | `reprocessed_data/{obs}/` | Calibrated event list |
| `acisf{obs}_repro_bpix1.fits` | `reprocessed_data/{obs}/` | Bad pixel file |

#### Step 3: Deflaring

| File | Location | Contents |
|------|----------|----------|
| `{obs}_0.5-7_thresh.img` | `reprocessed_data/{obs}/` | Counts image |
| `{obs}_0.5-7_thresh.expmap` | `reprocessed_data/{obs}/` | Exposure map |
| `{obs}_0.5-7.psf` | `reprocessed_data/{obs}/` | PSF size map |
| `{obs}_src_0.5-7.fits` | `reprocessed_data/{obs}/` | Point source catalog |
| `{obs}_src_0.5-7-noem.reg` | `reprocessed_data/{obs}/` | Point source regions |
| `{obs}_0.5-7.lc` | `reprocessed_data/{obs}/` | Light curve |
| `{obs}_0.5-7.gti` | `reprocessed_data/{obs}/` | Good time intervals |
| `acisf{obs}_clean_evt.fits` | `reprocessed_data/{obs}/` | Flare-filtered events |
| `{obs}_background_clean.evt` | `reprocessed_data/{obs}/` | Blank-sky background |

#### Step 4: Merging

| File | Location | Contents |
|------|----------|----------|
| `merged_evt.fits` | `merge_{name}_{smooth}_{sn}/` | Combined events |
| `broad_thresh.img` | `merge_{name}_{smooth}_{sn}/` | Merged counts |
| `broad_flux.img` | `merge_{name}_{smooth}_{sn}/` | Merged flux |
| `broad_thresh.expmap` | `merge_{name}_{smooth}_{sn}/` | Merged exposure |

#### Step 5: Flux Scaling

| File | Location | Contents |
|------|----------|----------|
| `scaled_broad_flux.fits` | `merge_{name}_{smooth}_{sn}/` | Scaled flux for binning |

#### Step 6: Cleaning

| File | Location | Contents |
|------|----------|----------|
| `broad_thresh_noem.img` | `merge_{name}_{smooth}_{sn}/` | Counts without cluster |
| `scaled_broad_flux_cropped.fits` | `merge_{name}_{smooth}_{sn}/` | Flux without point sources |
| `scaled_broad_flux_final.fits` | `merge_{name}_{smooth}_{sn}/`, `map_files/` | Final clean flux |

#### Step 7: Contour Binning

| File | Location | Contents |
|------|----------|----------|
| `contbin_binmap.fits` | `spec_files/contbin_sn{N}_smooth{M}/` | Bin assignments |
| `contbin_sn.fits` | `spec_files/contbin_sn{N}_smooth{M}/` | S/N map |
| `xaf_{i}.reg` | `spec_files/contbin_sn{N}_smooth{M}/outreg/` | Bin regions (physical) |

#### Step 8: Coordinate Conversion

| File | Location | Contents |
|------|----------|----------|
| `xaf_{i}_sex.reg` | `spec_files/contbin_sn{N}_smooth{M}/outreg/sex/` | Bin regions (WCS) |

---

## Physical Quantities Reference

### Energy Units

| Unit | Value | Use |
|------|-------|-----|
| keV | 1 keV = 1.602 × 10⁻⁹ erg | X-ray photon energy |
| eV | 1 eV = 1.602 × 10⁻¹² erg | ACIS PI channel width |
| PI channel | ~14.6 eV | ACIS energy digitization |

### Angular Units

| Unit | Value | Use |
|------|-------|-----|
| arcsec (") | 1/3600 degree | PSF size, small regions |
| arcmin (') | 1/60 degree | Cluster size |
| ACIS pixel | 0.492 arcsec | Native detector resolution |

### Count Rate Units

| Unit | Meaning |
|------|---------|
| counts | Raw detected photons |
| counts/s | Count rate |
| counts/s/arcmin² | Surface brightness |
| photons/cm²/s | Flux (exposure-corrected) |

### Temperature

| Unit | Conversion | Typical Values |
|------|------------|----------------|
| keV | Standard X-ray unit | 2-15 keV for clusters |
| K | T(K) = T(keV) × 1.16 × 10⁷ | 2×10⁷ - 2×10⁸ K |

### Signal-to-Noise Relationships

For source-dominated regime (clusters):
$$
\text{S/N} \approx \sqrt{N_{\text{source}}}
$$

Counts needed for target S/N:
$$
N \approx (\text{S/N})^2
$$

| S/N | Counts Needed |
|-----|---------------|
| 30 | 900 |
| 50 | 2,500 |
| 70 | 4,900 |
| 100 | 10,000 |

---

## References

1. **CIAO Software:** Fruscione et al. (2006), SPIE 6270, 62701V
2. **Contour Binning:** Sanders (2006), MNRAS 371, 829
3. **Wavdetect:** Freeman et al. (2002), ApJS 138, 185
4. **Chandra Proposers' Guide:** https://cxc.harvard.edu/proposer/POG/
5. **CALDB:** https://cxc.harvard.edu/caldb/
6. **Blank-Sky Backgrounds:** Hickox & Markevitch (2006), ApJ 645, 95

---

*Pipeline documentation for Chandra X-ray galaxy cluster analysis*  
*Last updated: 2026-02-03*
