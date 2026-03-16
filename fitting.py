import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import os

from bs_corr import correct_baseline
from fitting_helpers import mult_gaussian_with_horizontal_background, gaussian, mult_gaussian_with_linear_background, mult_gaussian, nearest_intensity
from config import config
from read_excel import read_excel


#create results directory if it doesn't exist
if not os.path.exists('./results'):
    os.makedirs('./results')

def fit_currents(long_df = None, bs_method: str = 'manual_poly', normalize: bool = False, plot: bool = True, **kwargs):
    # Temporarily prefer Arial for this function only
    old_font = plt.rcParams.get("font.family", None)
    plt.rcParams["font.family"] = "Arial"

    results = []
    long_df = long_df if long_df is not None else pd.read_csv("./data/long_df.csv")

    for current in long_df['sample'].unique():
        df_current = long_df[long_df['sample'] == current]
        for exp in df_current['experiment'].unique():
            print(f"Fitting experiment: {current} / {exp}")
            df = df_current[df_current['experiment'] == exp]
            df = df[df['wn'] > 2900] # Remove data before 2900 cm^-1
            wn = df['wn'].values
            int = df['int'].values

            if len(int) == 0:
                print(f"Skipping {current} / {exp} because no points > 2900 cm^-1")
                continue

            # Baseline correction: returns corrected intensity and params (including baseline)
            if normalize:
                int = int / int[-1]

            if bs_method == 'integrated':
                int_corr = int
                params_bs = {'baseline': np.zeros_like(int)}
                initial_slope, initial_intercept = np.polyfit(
                    np.concatenate([wn[5:27], wn[-22:]]),
                    np.concatenate([int[5:27], int[-22:]]),
                    1,
                )
            elif bs_method == 'manual_poly':
                int_corr, params_bs = correct_baseline(int, method='manual_poly', **kwargs)
                slope, intercept = np.polyfit(
                    np.concatenate([wn[5:27], wn[-22:]]),
                    params_bs['baseline'],
                    1,
                )
                int_corr = int - (intercept + slope * wn)
                params_bs['baseline'] = intercept + slope * wn
            else:
                int_corr, params_bs = correct_baseline(int, method=bs_method, **kwargs)

            baseline = params_bs['baseline']

            params = []
            lower_bounds = []
            upper_bounds = []
            peak_indices = []

            # Add linear background parameters for integrated method
            if bs_method == 'integrated':
                # mult_gaussian_with_linear_background expects [intercept, slope, ...]
                params.extend([initial_intercept, initial_slope])
                # Very loose bounds for background parameters
                lower_bounds.extend([-1e6, -1e6])
                upper_bounds.extend([1e6, 1e6])
            for peak in config["peaks"]:
                if config["peaks"][peak]["fit"]:
                    peak_indices.append(peak)
                    int_peak = max(nearest_intensity(config["peaks"][peak]["initial_position"], wn, int_corr), 100)
                    params.append(config["peaks"][peak]["initial_position"])
                    params.append(int_peak)
                    params.append(config["peaks"][peak]["initial_fwhm"])
                    lower_bounds.append(config["peaks"][peak]["position_bounds"][0])
                    upper_bounds.append(config["peaks"][peak]["position_bounds"][1])
                    lower_bounds.append(0)
                    upper_bounds.append(100000)
                    lower_bounds.append(config["peaks"][peak]["fwhm_bounds"][0])
                    upper_bounds.append(config["peaks"][peak]["fwhm_bounds"][1])
            
            bounds = [tuple(lower_bounds), tuple(upper_bounds)]
            # Fit on baseline-corrected intensity
            if bs_method == 'integrated':
                popt, pcov = curve_fit(mult_gaussian_with_linear_background, wn, int_corr, p0=params, bounds=bounds)
                fit_int = mult_gaussian_with_linear_background(wn, *popt)
                baseline = popt[0] + popt[1] * wn
            else:   
                popt, pcov = curve_fit(mult_gaussian, wn, int_corr, p0=params, bounds=bounds)
                fit_int = mult_gaussian(wn, *popt)
            
            peak_params = []
            start_params = len(params) % 3
            for peak_idx in range(start_params, len(params)-start_params, 3):
                pos, amp, fwhm = popt[peak_idx : peak_idx + 3]
                peak_params.append([pos, amp, fwhm])

            # Total fit including baseline
            total_fit = fit_int if bs_method == 'integrated' else baseline + fit_int
            fit_res = int - total_fit

            params_dict = {
                "sample": current,
                "experiment": exp,
                "wn": wn,
                "intensity": int,
                "baseline": baseline,
                "intensity_corrected": int_corr,
                "peak_params": peak_params,
                "popt": popt,
                "pcov": pcov,
                "fit_total": total_fit,
                "residuals": fit_res,
            }

            results.append(params_dict)

            fig, ax = plt.subplots(2, 1, figsize=(8, 8))
            ax[0].plot(wn, int, color='black', label='Data')
            ax[0].plot(wn, total_fit, color='red', label='Fitted')
            ax[0].plot(wn, baseline, color='orange', label='Baseline')
            for peak_idx in range(start_params, len(params)-start_params, 3):
                pos, amp, fwhm = popt[peak_idx : peak_idx + 3]
                ax[0].plot(wn, baseline + amp * np.exp(-(np.power(wn-pos,2)/(fwhm*fwhm/4.0/np.log(2.0)))), label=f'Gaussian {peak_idx//3 + 1}')
                ax[0].fill_between(wn, baseline + amp * np.exp(-(np.power(wn-pos,2)/(fwhm*fwhm/4.0/np.log(2.0)))), baseline, alpha=0.4)
            # Legend in two columns in the bottom-left of the main panel
            ax[0].legend(
                frameon=False,
                fontsize=14,
                ncol=2,
                loc="lower left",
            )
            ax[1].scatter(wn, fit_res, color='black', label='Residuals')
            # Print R2 score in red inside the plot (4 decimal places)
            r2 = 1 - np.sum(fit_res**2) / np.sum((int - np.mean(int))**2)
            ax[1].text(0.15, 0.92, f'R$^{2}$: {r2:.4f}', color='red', transform=ax[1].transAxes, fontsize=16)
            ax[1].legend(frameon=False, fontsize=16)
            ax[1].set_xlabel('Raman shift (cm$^{-1}$)', fontsize=16)
            ax[1].set_ylabel('Residuals (a.u.)', fontsize=16)
            ax[0].set_xlabel('Raman shift (cm$^{-1}$)', fontsize=16)
            ax[0].set_ylabel('Intensity (a.u.)', fontsize=16)
            ax[0].tick_params(axis='both', which='major', labelsize=16)
            ax[0].tick_params(axis='both', which='minor', labelsize=16)
            ax[1].tick_params(axis='both', which='major', labelsize=16)
            ax[1].tick_params(axis='both', which='minor', labelsize=16)

            # Tighten layout to minimize internal whitespace
            fig.tight_layout()

            # Save with tight bounding box to trim outer margins,
            # making each saved fit figure as compact as possible
            fig.savefig(
                f"./results/fit_current_{current}_exp_{exp}.png",
                dpi=300,
                bbox_inches="tight",
            )
            plt.close()



    if plot:
        plt.show()

    # Restore previous global font setting
    if old_font is not None:
        plt.rcParams["font.family"] = old_font

    rows = []
    for res in results:
        for i, peak in enumerate(res["peak_params"]):
            rows.append(
                {
                    "sample": res["sample"],
                    "experiment": res["experiment"],
                    "peak_index": i + 1,
                    "position": peak[0],
                    "amplitude": peak[1],
                    "fwhm": peak[2],
                }
            )

    params_df = pd.DataFrame(rows)
    params_df.to_csv("./results/fit_peak_params.csv", index=False)
    return params_df

if __name__ == "__main__":
    long_df = read_excel()
    params_df = fit_currents(long_df, plot=False, normalize=False, bs_method='manual_poly')
    print(params_df)
