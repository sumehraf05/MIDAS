# MIDAS: Micro-Electron Diffraction Integrated Data Automation System

An automated pipeline for processing Micro-Electron Diffraction (microED)
datasets. The workflow completely handles everything from raw image files
through to an optimally merged final dataset with minimum user intervention.

---
 
## What This Does
 
MicroED uses electron diffraction to determine atomic structures from
nanocrystals too small for traditional X-ray crystallography. Because each
crystal can only be measured briefly before radiation damage and the TEM stage
limits the angular range, data from many crystals must be combined. MIDAS
automates that entire process:
 
- **Data processing** — renames files, generates XDS.INP, runs XDS with
  adaptive spot finding, excludes bad frames and ice rings, and extracts
  quality statistics for every crystal
- **Quality filtering** — identifies the dominant crystal form using
  statistical outlier detection, re-indexes datasets that drifted from the
  consensus cell, and ranks compatible datasets by quality score
- **Optimal merging** — merges all compatible datasets with XSCALE, then
  uses greedy forward selection to find the subset that maximises completeness
  while keeping Rmeas and CC½ high
- **Output** — produces a merged XSCALE.HKL and a SHELX-format shelx.hkl
  ready for structure determination, plus a timestamped log file
---
 
## Repository
 
```
https://github.com/sumehraf05/MIDAS
```
 
| File | Description |
|------|-------------|
| `xds_pipeline.py` | Main pipeline — runs everything end to end |
| `microed_cnn.py` | Neural network module — model, preprocessing, inference |
| `train_cnn.py` | Training script — teaches the CNN using XDS results |
| `instrument_config.py` | Loader for the instrument config YAML (defaults + overrides) |
| `instrument_config.yaml` | Per-instrument/per-session parameters (beam centre, gain, etc.) — edit this, not the script |
| `TUTORIAL.md` | Step-by-step SOP with acetaminophen worked example |
| `LICENSE` | MIT License |
 
---
 
## Requirements
 
### 1. Clone the repository
 
```bash
git clone https://github.com/sumehraf05/MIDAS.git
cd MIDAS
```
 
### 2. Install Anaconda or Miniconda
 
Download from https://www.anaconda.com/download or
https://docs.conda.io/en/latest/miniconda.html
 
### 3. Create the conda environment
 
```bash
conda create -n xds
conda activate xds
conda install -c conda-forge watchdog fabio numpy pyyaml
conda install -c pytorch pytorch torchvision
```
 
> **Note:** Install `torch` and `torchvision` via conda rather than pip.
> Using `pip install torch` inside a conda environment can cause import
> errors even when the installation appears to succeed.
>
> `pyyaml` is required for `--config` support (reading
> `instrument_config.yaml`). It's a near-universal transitive dependency of
> scientific Python environments, so it's often already present — the
> `conda install` above makes sure of it.
 
### 4. Activate the environment before running
 
```bash
conda activate xds
```
 
### 5. Install XDS
 
XDS must be installed and on your PATH. Download from https://xds.mr.mpg.de
 
```bash
cd ~
wget https://xds.mr.mpg.de/XDS-gfortran_Linux_x86_64.tar.gz
tar -xzf XDS-gfortran_Linux_x86_64.tar.gz
 
# Add to PATH (add to ~/.bashrc to make permanent)
export PATH=~/XDS-gfortran_Linux_x86_64:$PATH
 
# Verify installation
which xds_par
xds_par | head -4
```
 
---
 
## Quick Start
 
```bash
# Step 1: Process all crystals through XDS and merge with XSCALE
python3 xds_pipeline.py --folder /path/to/your/data --config instrument_config.yaml
 
# Step 2: Train the CNN on your results
python3 train_cnn.py
 
# Step 3: Re-run with CNN quality scores feeding into dataset selection
python3 xds_pipeline.py --folder /path/to/your/data --config instrument_config.yaml
```
 
After each run the pipeline automatically produces two output files in
`xscale/optimal/`:
- `XSCALE.HKL` — merged dataset in XDS format
- `shelx.hkl` — same data converted to SHELX format, ready for structure
  determination with SHELXS or SHELXL
See `TUTORIAL.md` for a complete step-by-step walkthrough using
acetaminophen as a worked example.
 
---
 
## Running the Pipeline
 
```bash
python3 xds_pipeline.py
```
 
When prompted, drag your parent folder (the one containing all your crystal
subdirectories) into the terminal and press Enter.
 
Your folder structure should look like this:
 
```
parent_folder/
    crystal-1/
        crystal-1_0001.img
        crystal-1_0002.img
        ...
    crystal-2/
        crystal-2_0001.img
        ...
```
 
### Command line options
 
```bash
# Pass the folder path directly (skips the interactive prompt)
python xds_pipeline.py --folder /path/to/your/data

# Use an instrument config file (beam centre, gain, oscillation, untrusted
# regions, etc. — see "Instrument Configuration" below). If omitted, the
# pipeline falls back to the UCSC Glacios/CETA defaults.
python xds_pipeline.py --folder /path/to/your/data --config instrument_config.yaml

# If you already know the unit cell and/or space group, provide them to
# dramatically improve indexing on difficult datasets
python xds_pipeline.py --folder /path/to/your/data \
    --unit-cell "9.44 9.44 15.23 89.7 89.8 60.2" --space-group 2

# Process multiple crystals in parallel (recommended: 4-8 on a server)
python xds_pipeline.py --folder /path/to/your/data --workers 4
 
# Watch mode: keep running and process new crystals as they appear
python xds_pipeline.py --folder /path/to/your/data --watch
 
# Run in the background so the job continues after you close the terminal
nohup python xds_pipeline.py --folder /path/to/your/data --workers 4 > pipeline.log 2>&1 &
 
# Monitor a background run
tail -f pipeline.log
```

> **Note on `--space-group`:** this defaults to `0`, which lets XDS
> determine the space group itself rather than forcing everything into P1.
> A consistent space group across your datasets is itself a useful quality
> signal — forcing P1 throws that signal away. Only pass an explicit value
> (e.g. `--space-group 2` for P-1) if you already know it.
 
---
 
## Output
 
After a successful run, your data folder will contain:
 
```
parent_folder/
    cell_parameters_summary.csv           # Quality metrics for every crystal
    parent_folder_YYYYMMDD_HHMMSS.log     # Timestamped log of the full run
    crystal-1/
        XDS.INP                           # XDS configuration (auto-generated)
        XDS_ASCII.HKL                     # Processed reflections
        CORRECT.LP                        # XDS statistics log
        IDXREF.LP                         # Indexing log
        log/
            crystal-1_XDS_idxref.log
            crystal-1_XDS_integrate.log
    xscale/
        all_compatible/
            XSCALE.HKL                    # All compatible datasets merged
        optimal/
            XSCALE.HKL                    # Best subset merged (use this)
            shelx.hkl                     # SHELX format for structure solution
        trials/                           # One folder per greedy search step
```
 
**The file to use for structure determination is `xscale/optimal/XSCALE.HKL`.**  
**The SHELX-format file ready for SHELXS/SHELXL is `xscale/optimal/shelx.hkl`.**
 
---
 
## How Dataset Selection Works
 
**Filter 1 — Dominant crystal form:** For each unit cell parameter the pipeline
computes the median and median absolute deviation (MAD). Any dataset more than
3 MADs from the median is automatically rejected as a wrong indexing solution
or incompatible crystal form. An absolute tolerance check (2 Å / 5°) is then
applied as a second pass.

Datasets excluded at this step are labelled either "Wrong cell" or "Possible
multi-lattice," based on their indexed fraction — a dataset that indexed a
moderate fraction of spots (roughly 15–55%) is more likely to be a
multi-lattice crystal (overlapping lattices from more than one crystallite)
than a wholly wrong indexing solution, and is worth a manual look rather than
writing off outright. This is a heuristic, not a definitive diagnosis.
 
**Consensus cell correction:** After the initial run, the pipeline computes
the consensus cell and re-indexes any crystal that deviates by more than
1.5 Å or 3°. This corrects datasets where XDS picked an alternative
indexing solution rather than the true lattice. Re-indexing seeds the known
or consensus space group (see `--space-group` above) rather than forcing P1.
 
**Filter 2 — Quality ranking:** Compatible datasets are ranked by a composite
quality score (indexed fraction, completeness, I/sigma, CNN score).
 
**Greedy forward selection:** Starting with the best dataset, each remaining
dataset is tested by running XSCALE with it included. It is kept only if the
merged completeness, CC½, and Rmeas all genuinely improve. Note this is a
greedy heuristic, not a guaranteed globally-optimal subset — it can miss a
better combination that isn't reachable by adding datasets one at a time in
ranked order. Exhaustive subset search is exponential, so this is a
deliberate tradeoff.
 
**Resolution extension:** The final merge uses the best individual resolution
limit extended by 0.1 Å (capped at 0.80 Å) to maximise high-resolution content.
 
---
 
## How the Neural Network Works
 
`microed_cnn.py` contains a ResNet-18 based convolutional neural network
adapted for single-channel grayscale diffraction images with two outputs:
 
**Unit cell prediction** — independently predicts the six cell parameters from
raw diffraction images and compares against XDS. Disagreements of more than
5 Å or 5° flag the dataset for review.
 
**Quality scoring** — predicts a 0–1 quality score from image features such as
spot sharpness and signal-to-background ratio. Run `train_cnn.py` after the
pipeline has processed your data to train the network on your own results.

The pipeline looks for the trained weights file (`microed_cnn_weights.pt`)
inside your data folder — the same folder `train_cnn.py` writes it to — not
in whatever directory you happen to run the script from. The resolved path
is printed at startup ("Looking for CNN weights at: ...") so you can confirm
it's finding the right file.
 
---
 
## Instrument Configuration

Instrument-specific parameters — beam centre, rotation axis, gain,
oscillation range, detector distance/wavelength fallbacks, and untrusted
detector regions — live in a config YAML (`instrument_config.yaml`) rather
than being hardcoded in `xds_pipeline.py`. Pass it with `--config`:

```bash
python xds_pipeline.py --folder /path/to/your/data --config instrument_config.yaml
```

Any value you omit from your config file falls back to the UCSC
Glacios/CETA defaults below. If you don't pass `--config` at all, those
defaults are used for everything.

```yaml
beam_center: [1043.0, 1046.0]   # ORGX, ORGY -- measure fresh each session, it drifts
rotation_axis: [0, 1, 0]
gain: 15
oscillation_range: 1.0          # degrees/frame -- adjust for small molecule vs protein
detector_distance: null         # null = read from image header; fallback if missing
wavelength: null                # null = read from image header; fallback if missing
detector: ADSC
nx: 2048
ny: 2048
qx: 0.028
qy: 0.028
overload: 65000
untrusted_ellipse: null         # e.g. [966, 1115, 980, 1120]; null = skip masking
untrusted_quadrilateral: null   # e.g. [992, 1024, 1, 1056, 2, 1113, 990, 1072]
sepmin: 7.0
cluster_radius: 3.5
```

The pipeline is currently configured by default for the UCSC Biomolecular
Cryo-EM Facility using a ThermoFisher Scientific Glacios 200 kV cryo-TEM
with a CETA 16M detector operated in 2×2 binning mode:

| Parameter | Default value | Description |
|-----------|-------|-------------|
| `DETECTOR` | ADSC | XDS detector type identifier |
| `NX` / `NY` | 2048 / 2048 | Detector size in pixels (2×2 binned from 4096×4096) |
| `QX` / `QY` | 0.028 mm | Effective pixel size (14 µm native × 2 binning) |
| `ORGX` / `ORGY` | 1043 / 1046 | Beam centre in pixels — drifts between sessions; re-measure and set in your config each time |
| `X-RAY_WAVELENGTH` | 0.025082 Å | Electron wavelength at 200 kV |
| `GAIN` | 15 | Detector gain |
| `OVERLOAD` | 65000 | Pixel saturation threshold |
| `OSCILLATION_RANGE` | 1.0 deg | Rotation per frame |

Detector distance and wavelength are read automatically from the image
header (`DETECTOR_DISTANCE`/`DISTANCE` and `WAVELENGTH` keys) when present;
otherwise the `detector_distance`/`wavelength` values from your config are
used, falling back to the UCSC defaults if those are also `null`.

If you're on a different instrument or detector, copy
`instrument_config.yaml`, fill in your own values, and pass it with
`--config` — you shouldn't need to touch `xds_pipeline.py` itself.
 
---
 
## Troubleshooting
 
**XDS not on PATH:**
```bash
export PATH=~/XDS-gfortran_Linux_x86_64:$PATH
```
 
**XDS license expired:** Download the latest version from https://xds.mr.mpg.de
 
**0 datasets processed:** Check that `.img` files exist inside subdirectories:
```bash
find /path/to/data -name "*.img" | head -5
```
 
**-99.9% Rmeas:** Each reflection was measured only once (multiplicity = 1).
This is normal for individual microED datasets — XSCALE merging builds redundancy.
 
**CNN not loading:** Run `train_cnn.py` first, and make sure
`microed_cnn_weights.pt` ends up in your data folder (the one you pass to
`--folder`) — that's where the pipeline looks for it. The startup log line
"Looking for CNN weights at: ..." shows the exact path it checked. The
pipeline still runs without it.
 
**torch import error:** Make sure torch was installed via conda and not pip:
```bash
conda install -c pytorch pytorch torchvision
```
 
**shelx.hkl not produced:** Check that `xdsconv` is on your PATH:
```bash
which xdsconv
```
`xdsconv` is included with XDS and should be available once XDS is installed.

**Low indexed fraction / fewer datasets indexing than expected:** Double
check your `instrument_config.yaml` beam centre first — it's the single
most common cause and it drifts between sessions. If indexing is still
poor, consider passing `--unit-cell` with a known cell to help XDS lock
onto the correct lattice.

**A dataset is excluded as "Possible multi-lattice":** this means its
indexed fraction fell in a range (roughly 15–55%) that's often associated
with overlapping lattices from more than one crystallite, rather than a
simple wrong-cell indexing failure. It's flagged for a manual look, not
automatically salvaged — the pipeline doesn't currently attempt to
deconvolute multi-lattice data.
 
---
 
## Citation
 
If you use MIDAS in your research, please cite:
 
> Ferdous, S. *MIDAS: Micro-Electron Diffraction Integrated Data Automation System.*
> University of California, Santa Cruz (2026).
> https://github.com/sumehraf05/MIDAS
 
---
 
## License
 
Copyright © 2026 The Regents of the University of California.  
Distributed under the MIT License. See `LICENSE` for more information.
