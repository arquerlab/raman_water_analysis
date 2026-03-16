# Anku Data Analysis

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