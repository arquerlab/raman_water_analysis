from __future__ import annotations

import os
from typing import Iterable, Optional
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from .baseline import correct_baseline
from .config import config
from .models import mult_gaussian, mult_gaussian_with_linear_background
from .io import default_results_dir, nearest_intensity


def _ensure_results_dir(results_dir: str) -> None:
    """Create the results directory if it does not exist."""
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)


def fit_currents(
    long_df: Optional[pd.DataFrame] = None,
    bs_method: str = "manual_poly",
    normalize: bool = False,
    plot: bool = True,
    results_dir: Optional[str] = None,
    **kwargs,
) -> pd.DataFrame:
    """
    Fit spectra as a function of current and write out parameters and figures.

    This is a refactored version of the original top-level ``fit_currents``
    that allows the caller to specify a results directory and provide
    an already-loaded long dataframe.
    """
    if results_dir is None:
        results_dir = str(default_results_dir())

    _ensure_results_dir(results_dir)

    old_font = plt.rcParams.get("font.family", None)
    plt.rcParams["font.family"] = "Arial"

    results: list[dict] = []
    if long_df is None:
        # Fall back to long_df.csv if not provided.
        # For per-subfolder runs, long_df.csv is expected to be inside results_dir.
        candidate_paths = [
            os.path.join(results_dir, "long_df.csv"),
            os.path.join(os.path.dirname(results_dir), "data", "long_df.csv"),
        ]
        for candidate in candidate_paths:
            if os.path.exists(candidate):
                long_df = pd.read_csv(candidate)
                break
        else:
            raise FileNotFoundError(
                "long_df was not provided and long_df.csv could not be found. "
                f"Tried: {', '.join(candidate_paths)}"
            )

    exp_id = 0

    for current in long_df["sample"].unique():
        df_current = long_df[long_df["sample"] == current]
        for exp in df_current["experiment"].unique():
            print(f"Fitting experiment: {current} / {exp}")
            df = df_current[df_current["experiment"] == exp]
            df = df[df["wn"] > 2900]
            wn = df["wn"].values
            intensity = df["int"].values

            if len(intensity) == 0:
                print(f"Skipping {current} / {exp} because no points > 2900 cm^-1")
                continue

            if normalize:
                intensity = intensity / intensity[-1]

            if bs_method == "integrated":
                int_corr = intensity
                params_bs = {"baseline": np.zeros_like(intensity)}
                initial_slope, initial_intercept = np.polyfit(
                    np.concatenate([wn[5:27], wn[-22:]]),
                    np.concatenate([intensity[5:27], intensity[-22:]]),
                    1,
                )
            elif bs_method == "manual_poly":
                int_corr, params_bs = correct_baseline(intensity, method="manual_poly", **kwargs)
                slope, intercept = np.polyfit(
                    np.concatenate([wn[5:27], wn[-22:]]),
                    params_bs["baseline"],
                    1,
                )
                int_corr = intensity - (intercept + slope * wn)
                params_bs["baseline"] = intercept + slope * wn
            else:
                int_corr, params_bs = correct_baseline(intensity, method=bs_method, **kwargs)

            baseline = params_bs["baseline"]

            params: list[float] = []
            lower_bounds: list[float] = []
            upper_bounds: list[float] = []

            if bs_method == "integrated":
                params.extend([initial_intercept, initial_slope])
                lower_bounds.extend([-1e6, -1e6])
                upper_bounds.extend([1e6, 1e6])

            for peak in config["peaks"]:
                if config["peaks"][peak]["fit"]:
                    int_peak = max(
                        nearest_intensity(config["peaks"][peak]["initial_position"], wn, int_corr),
                        100,
                    )
                    params.append(config["peaks"][peak]["initial_position"])
                    params.append(int_peak)
                    params.append(config["peaks"][peak]["initial_fwhm"])
                    lower_bounds.append(config["peaks"][peak]["position_bounds"][0])
                    upper_bounds.append(config["peaks"][peak]["position_bounds"][1])
                    lower_bounds.append(0)
                    upper_bounds.append(100000)
                    lower_bounds.append(config["peaks"][peak]["fwhm_bounds"][0])
                    upper_bounds.append(config["peaks"][peak]["fwhm_bounds"][1])

            bounds = (tuple(lower_bounds), tuple(upper_bounds))

            if bs_method == "integrated":
                popt, pcov = curve_fit(
                    mult_gaussian_with_linear_background, wn, int_corr, p0=params, bounds=bounds
                )
                fit_int = mult_gaussian_with_linear_background(wn, *popt)
                baseline = popt[0] + popt[1] * wn
            else:
                popt, pcov = curve_fit(mult_gaussian, wn, int_corr, p0=params, bounds=bounds)
                fit_int = mult_gaussian(wn, *popt)

            peak_params = []
            fitted_peak_names = [name for name, v in config["peaks"].items() if v.get("fit", False)]
            start_params = len(params) % 3
            for peak_idx in range(start_params, len(params) - start_params, 3):
                pos, amp, fwhm = popt[peak_idx : peak_idx + 3]
                peak_params.append([pos, amp, fwhm])

            total_fit = fit_int if bs_method == "integrated" else baseline + fit_int
            fit_res = intensity - total_fit

            params_dict = {
                "sample": current,
                "experiment": exp,
                "wn": wn,
                "intensity": intensity,
                "baseline": baseline,
                "intensity_corrected": int_corr,
                "peak_params": peak_params,
                "peak_names": fitted_peak_names,
                "popt": popt,
                "pcov": pcov,
                "fit_total": total_fit,
                "residuals": fit_res,
            }
            results.append(params_dict)

            exp_id += 1

    if plot:
        plt.show()

    if old_font is not None:
        plt.rcParams["font.family"] = old_font

    rows: list[dict] = []
    peak_index_by_name = {"membrane": 1, "4hb": 2, "3hb": 3, "0hb": 4}
    for res in results:
        for i, peak in enumerate(res["peak_params"]):
            peak_name = None
            if "peak_names" in res and i < len(res["peak_names"]):
                peak_name = res["peak_names"][i]
            peak_index = peak_index_by_name.get(str(peak_name).lower(), i + 1)
            rows.append(
                {
                    "sample": res["sample"],
                    "experiment": res["experiment"],
                    "peak_index": peak_index,
                    "peak_name": peak_name,
                    "position": peak[0],
                    "amplitude": peak[1],
                    "fwhm": peak[2],
                }
            )

    params_df = pd.DataFrame(rows)
    params_df.to_csv(os.path.join(results_dir, "fit_peak_params.csv"), index=False)

    # Save full per-experiment fit traces in a compact, reloadable format.
    # JSON is not suitable here because it cannot store ndarrays without
    # converting to huge nested lists.
    fit_traces_dir = os.path.join(results_dir, "fit_traces_npz")
    _ensure_results_dir(fit_traces_dir)

    manifest: list[dict] = []

    def _slug(text: str) -> str:
        safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in str(text))
        while "__" in safe:
            safe = safe.replace("__", "_")
        return safe.strip("_")

    for res in results:
        sample = str(res["sample"])
        experiment = str(res["experiment"])
        base = f"{_slug(sample)}__{_slug(experiment)}"
        npz_name = f"{base}.npz"
        npz_path = os.path.join(fit_traces_dir, npz_name)

        peak_params_arr = np.asarray(res["peak_params"], dtype=float)

        np.savez_compressed(
            npz_path,
            sample=sample,
            experiment=experiment,
            wn=np.asarray(res["wn"]),
            intensity=np.asarray(res["intensity"]),
            baseline=np.asarray(res["baseline"]),
            intensity_corrected=np.asarray(res["intensity_corrected"]),
            peak_params=peak_params_arr,
            popt=np.asarray(res["popt"]),
            pcov=np.asarray(res["pcov"]),
            fit_total=np.asarray(res["fit_total"]),
            residuals=np.asarray(res["residuals"]),
        )

        manifest.append(
            {
                "sample": sample,
                "experiment": experiment,
                "npz": os.path.relpath(npz_path, results_dir),
                "n_points": int(len(res["wn"])),
                "n_components": int(peak_params_arr.shape[0]) if peak_params_arr.ndim == 2 else None,
            }
        )

    with open(os.path.join(results_dir, "fit_traces_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return params_df, results

