# Water Data Analysis

This repository contains the analysis code used to fit current-dependent spectral data and generate the figures and summary tables used in the accompanying study. The workflow takes raw/processed fit results, aggregates peak parameters, and produces publication-ready multi-panel figures and derived quantities (percentages, Stark slopes, etc.).

---

## Repository structure (current)

- `src/water_analysis/`  
  Core analysis package:
  - `io.py`: reading the spectroscopy Excel file, constructing the long-format dataframe, and writing `data/long_df.csv`.
  - `fitting.py`: `fit_currents(...)` implementation, performing the spectral fits and writing `results/fit_peak_params.csv` and individual fit figures `results/fit_*_current_*_exp_*.png`.
  - `plotting.py`: `plot_fit_params(...)` implementation, aggregating parameters and generating all summary and multipanel figures plus intermediate CSVs.

- `scripts/`  
  Thin command-line entry points:
  - `scripts/run_full_analysis.py`: runs the complete pipeline (read Excel → fit → all figures).
  - `scripts/make_fit_summary_plots.py`: regenerates all summary and multipanel figures from an existing `results/fit_peak_params.csv`.

- `main.py`  
  Convenience entry point that mirrors `scripts/run_full_analysis.py` and uses the `water_analysis` package.

- `plot_fit_params.py`  
  Thin wrapper that imports `water_analysis.plotting.plot_fit_params` so existing workflows still work.

- `config.py` / `config.toml`  
  Provide the `config` dictionary (via TOML) that controls which peaks are fitted and plotted (e.g. `config["peaks"]["0hb"]["fit"]`).

- `data/`  
  - `current vs voltage.xlsx`: used in the Stark analysis to convert current (A) to cell voltage and compute Stark slopes (cm⁻¹/V).

- `results/`  
  Output directory for all generated files:
  - `fit_peak_params.csv` – input for `plot_fit_params` if not passing a DataFrame.
  - `fit_*_current_*_exp_*.png` – individual fit plots for each current/experiment combination.
  - `fit_peak_params_agg.csv` – aggregated amplitudes, FWHM, positions vs current density.
  - `fit_peak_params_percentages_data.csv` – derived percentages of total amplitude for selected species.
  - `fit_peak_params_stark_slopes_data.csv` – computed Stark slopes and uncertainties.
  - `fit_peak_params_united.(png|svg)` – united amplitude/FWHM/position vs current plots.
  - `fit_peak_params_single.(png|svg)` – multi-panel (per-species) summary plots.
  - `fit_peak_params_percentages.(png|svg)` – percentage vs current density.
  - `fit_peak_params_stark_slopes.(png|svg)` – Stark slope bar plots.
  - `fit_current_multipanel_*.{png,svg}` – 3×2 multipanel figures composing individual fit plots.

---

## Input Data Structure

### Dataset discovery (how folders are processed)
The full pipeline scans the default `data/` directory (or `data_root=` if you call it programmatically) and automatically processes every spectroscopy Excel file whose filename contains `_data` (case-insensitive), e.g.:

- `data/Ar/Ar_data.xlsx`
- `data/CO2/CO2_data.xlsx`

For each `*_data.xlsx` match:

1. The parent folder of the Excel file is treated as the dataset folder.
2. The pipeline expects an IV file named `current vs voltage.xlsx` in the same dataset folder.
   - If it is missing, it falls back to `data/current vs voltage.xlsx`.
3. Outputs are written to `results/<dataset_folder_relative_path>/`.

### Spectroscopy Excel file layout (`*_data.xlsx`)
The loader reads the Excel file with `pandas.read_excel(header=None, sheet_name=None)` and expects:

- One worksheet per current condition.
- Each worksheet name must start with the current value in **mA** as the first token, e.g. `50 mA`, `750 mA`.
  - This numeric prefix is parsed as `current_mA` (and also converted to `current_A = current_mA / 1000`).
- The worksheet named `4 mA` is skipped.
- Each worksheet contains multiple experiments stored as **alternating column pairs** with no header rows:
  - Columns `(0, 1)` = Raman shift `wn` (cm⁻¹) and intensity `int` for `exp1`
  - Columns `(2, 3)` = `wn` and `int` for `exp2`
  - Columns `(4, 5)` = `wn` and `int` for `exp3`
  - …and so on

Only the column pairs whose first `wn` value is >= 3000 cm⁻¹ are kept by the loader (others are ignored).

In practice: for each experiment you need two adjacent columns, `wn` then `int`.

### Current–Voltage Excel file layout (`current vs voltage.xlsx`)
The loader reads the IV file and uses:

- The first column as `current_A` (current in **A**).
- The second column as `cell_voltage` (cell voltage).

These values are matched by exact equality to `current_A` parsed from the spectroscopy sheet names, so you should ensure the numeric values align after converting mA -> A.

## Generated Plots and Tables

The plotting outputs are generated per dataset into `results/<dataset_folder_relative_path>/` (created automatically).

### Spectral fitting outputs
- `fit_{exp_id:02d}_current_{current}_exp_{exp}.png` (individual fits)
  - Two-panel figure: (1) spectrum data + total fit + fitted baseline + each Gaussian component, and (2) residuals.
- `fit_peak_params.csv`
  - Long table of fitted peak parameters per `sample` (current), `experiment`, and `peak_index` (`position`, `amplitude`, `fwhm`).

### Peak-parameter summary plots (from fitted peaks)
- `fit_peak_params_agg.csv`
  - Aggregated mean/std of `amplitude`, `fwhm`, and `position` grouped by `current_mA` and `peak_index`.
- `fit_peak_params_united.png` / `fit_peak_params_united.svg`
  - Three stacked errorbar plots vs `current_density (A·cm^-2)`:
    - amplitude vs current
    - FWHM vs current
    - Raman shift (position) vs current
- `fit_peak_params_single.png` / `fit_peak_params_single.svg`
  - Multi-panel summary for each fitted peak species:
    - 3 columns (Amplitude, FWHM, Raman shift)
    - number of rows depends on `config.toml` (it switches between a 2×3 and 3×3 grid depending on whether `peaks.0hb.fit` is enabled).

### Derived quantities
- `fit_peak_params_percentages_data.csv` and `fit_peak_params_percentages.png/svg`
  - Percentage of total amplitude (%) vs `current_density` for the selected water peaks (hard-coded in the plotting code to the fitted peak indices used for 4-HB water and 3-HB water).
- `fit_peak_params_stark_slopes_data.csv` and `fit_peak_params_stark_slopes.png/svg`
  - Stark slope analysis over three current-density intervals: `0.05–0.2`, `0.2–0.4`, `0.4–0.75` `A·cm^-2` (computed from the corresponding fitted peak positions at the matching current bounds)
  - Bottom panel: Stark slope bars (cm^-1 V^-1) for the two selected peaks.
  - Top panel: for one of those peaks, shows percentage bars with a Raman-shift line (using the same current-density points).

### Multipanel image grids
- `fit_current_multipanel_{i}.png` / `fit_current_multipanel_{i}.svg`
  - Created by stitching the individual fit figures (`fit_*_current_*_exp_*.png`) into 2×3 grids, with a title of the form `{current} / {exp}`.

## Run for a Single Subfolder

You can restrict processing to only one dataset subfolder under `data/` (e.g. `flow_cell`):

```bash
python scripts/run_full_analysis.py --subfolder flow_cell
```

---

## Software requirements

The analysis code is written in Python and uses:

- `numpy`
- `pandas`
- `matplotlib`
- `openpyxl` or a similar engine for reading Excel files (via `pandas.read_excel`)
- standard library modules (`os`, `glob`)

You can install the required packages, for example:

```bash
pip install numpy pandas matplotlib openpyxl
```

---
## License

MIT License

## Author

Adrián Pinilla-Sánchez - adpisa@gmail.com

---