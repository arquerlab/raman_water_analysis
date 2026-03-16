import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter
from matplotlib import colors as mcolors

from config import config


def plot_fit_params(fit_results = None):
    # Temporarily prefer Arial for this function only
    old_font = plt.rcParams.get("font.family", None)
    plt.rcParams["font.family"] = "Arial"

    df = fit_results if fit_results is not None else pd.read_csv("./results/fit_peak_params.csv")
    # Original current in mA (from sample label like "50 mA")
    df["current_mA"] = df["sample"].apply(lambda x: float(x.split()[0]))
    # Current density in A·cm^-2 (assuming 1 cm^2 area, i.e. mA -> A)
    df["current_density"] = df["current_mA"] / 1000.0
    df_use = df[df["current_mA"] != 4.0]

    capsize = 3
    marker = 'o'
    color_peak_4 = "#c8b9e5ff"  # was "#c8b9e540"
    color_peak_3 = "#78a3cfff"  # was "#78a3cf40"
    color_peak_2 = "#acac9fff"  # was "#acac9f40"
    color_peak_1 = "#c8b9e540"
    legend_frameon = False
    label_peak_4 = "0-HB"
    label_peak_3 = "3-HB water"
    label_peak_2 = "4-HB water"
    label_peak_1 = "Membrane"
    agg = (
        df_use
        .groupby(["current_mA", "current_density", "peak_index"], as_index=False)
        .agg(
            amp_mean=("amplitude", "mean"),
            amp_std=("amplitude", "std"),
            fwhm_mean=("fwhm", "mean"),
            fwhm_std=("fwhm", "std"),
            pos_mean=("position", "mean"),
            pos_std=("position", "std"),
        )
    )

    # Save aggregated data used in united/single plots
    agg_out = agg.copy()
    agg_out["species"] = agg_out["peak_index"].map(
        {1: label_peak_4, 2: label_peak_2, 3: label_peak_3, 4: label_peak_4}
    )
    agg_out.to_csv("./results/fit_peak_params_agg.csv", index=False)

    fig, ax = plt.subplots(3, 1, figsize=(5, 12))

    # Helper to enforce a minimum visible error size
    def min_err(values, errs, frac=0.02):
        values = np.asarray(values, dtype=float)
        errs = np.asarray(errs, dtype=float)
        data_range = values.max() - values.min()
        baseline = data_range * frac if data_range > 0 else max(abs(values.max()), 1.0) * frac
        return np.maximum(errs, baseline)

    # First figure: mean with error bars (std) for all peaks together
    for peak, color, label in zip(agg["peak_index"].unique()[1:], [color_peak_2, color_peak_3, color_peak_4], [label_peak_2, label_peak_3, label_peak_4]):
        df_peak = agg[agg["peak_index"] == peak].sort_values("current_density")
        x = df_peak["current_density"]

        amp_yerr = min_err(df_peak["amp_mean"], df_peak["amp_std"])
        fwhm_yerr = min_err(df_peak["fwhm_mean"], df_peak["fwhm_std"])
        pos_yerr = min_err(df_peak["pos_mean"], df_peak["pos_std"])

        ax[0].errorbar(x, df_peak["amp_mean"],  yerr=amp_yerr,  marker=marker, capsize=capsize, elinewidth=1.5, label=f'{label}', color=color)
        ax[1].errorbar(x, df_peak["fwhm_mean"], yerr=fwhm_yerr, marker=marker, capsize=capsize, elinewidth=1.5, label=f'{label}', color=color)
        ax[2].errorbar(x, df_peak["pos_mean"],  yerr=pos_yerr,  marker=marker, capsize=capsize, elinewidth=1.5, label=f'{label}', color=color)

    for a in ax:
        a.legend(frameon=legend_frameon)

    ax[0].set_ylabel('Amplitude')
    ax[1].set_ylabel('FWHM')
    ax[2].set_ylabel(r"Raman shift (cm$^{-1}$)")
    ax[2].set_xlabel(r"Current density (A·cm$^{-2}$)")
    # Force plain (non-scientific) formatting on position axis
    pos_formatter = ScalarFormatter(useMathText=False)
    pos_formatter.set_scientific(False)
    pos_formatter.set_useOffset(False)
    ax[2].yaxis.set_major_formatter(pos_formatter)

    ax[0].set_title('Amplitude vs. Current')
    ax[1].set_title('FWHM vs. Current')
    ax[2].set_title('Position vs. Current')

    #Tight layout
    #plt.tight_layout()

    #Save figure
    plt.savefig('./results/fit_peak_params_united.png')
    plt.savefig('./results/fit_peak_params_united.svg', dpi=300)
    plt.close()

    if config["peaks"]["0hb"]["fit"]:
        fig, ax = plt.subplots(3, 3, figsize=(15, 10))
    else:
        fig, ax = plt.subplots(2, 3, figsize=(15, 10))

    for i, peak, color, label in zip(range(len(agg["peak_index"].unique()[1:])), agg["peak_index"].unique()[1:], [color_peak_2, color_peak_3, color_peak_4], [label_peak_2, label_peak_3, label_peak_4]):
        df_peak = agg[agg["peak_index"] == peak].sort_values("current_density")
        x = df_peak["current_density"]

        amp_yerr = min_err(df_peak["amp_mean"], df_peak["amp_std"])
        fwhm_yerr = min_err(df_peak["fwhm_mean"], df_peak["fwhm_std"])
        pos_yerr = min_err(df_peak["pos_mean"], df_peak["pos_std"])

        ax[i, 0].errorbar(x, df_peak["amp_mean"],  yerr=amp_yerr,  marker=marker, capsize=capsize, elinewidth=1.5, label=f'{label}', color=color)
        ax[i, 1].errorbar(x, df_peak["fwhm_mean"], yerr=fwhm_yerr, marker=marker, capsize=capsize, elinewidth=1.5, label=f'{label}', color=color)
        ax[i, 2].errorbar(x, df_peak["pos_mean"],  yerr=pos_yerr,  marker=marker, capsize=capsize, elinewidth=1.5, label=f'{label}', color=color)

    for row in ax:
        for j, (col, ylabel) in enumerate(zip(row, ['Amplitude', 'FWHM', r'Raman shift (cm$^{-1}$)'])):
            col.set_ylabel(ylabel)
            col.set_xlabel('Current density (A·cm⁻²)')
            if j == 2:
                pos_formatter_grid = ScalarFormatter(useMathText=False)
                pos_formatter_grid.set_scientific(False)
                pos_formatter_grid.set_useOffset(False)
                col.yaxis.set_major_formatter(pos_formatter_grid)

    #Tight layout
    #plt.tight_layout()
    #Save figure
    plt.savefig('./results/fit_peak_params_single.png')
    plt.savefig('./results/fit_peak_params_single.svg', dpi=300)
    plt.close()

    # ------------------------------------------------------------------
    # 1) Figure: percentage of 4-HB water and 3-HB water vs current density
    # ------------------------------------------------------------------
    pct_rows = []
    for (current_mA, current_density), g in agg.groupby(["current_mA", "current_density"]):
        # Remove membrane (peak_index 1) from percentage calculations
        g_use = g[g["peak_index"] != 1]
        total_amp_mean = g_use["amp_mean"].sum()
        if total_amp_mean == 0:
            continue

        for _, row in g_use.iterrows():
            amp_mean = row["amp_mean"]
            amp_std = row["amp_std"]

            # Convert fraction to percentage
            pct_mean = amp_mean / total_amp_mean * 100.0
            # Approximate std on the percentage using only the peak's own std
            if amp_mean == 0:
                pct_std = 0.0
            else:
                pct_std = pct_mean * (amp_std / amp_mean)

            pct_rows.append(
                {
                    "current_density": current_density,
                    "peak_index": row["peak_index"],
                    "pct_mean": pct_mean,
                    "pct_std": pct_std,
                }
            )

    pct_df = pd.DataFrame(pct_rows)

    # Save percentage data (used in percentages and Stark panel a)
    pct_out = pct_df.copy()
    pct_out["species"] = pct_out["peak_index"].map(
        {2: label_peak_2, 3: label_peak_3}
    )
    pct_out.to_csv("./results/fit_peak_params_percentages_data.csv", index=False)

    fig_pct, ax_pct = plt.subplots(1, 1, figsize=(8, 4))
    for peak, color, label in zip(
        [2, 3], [color_peak_2, color_peak_3], [label_peak_2, label_peak_3]
    ):
        df_peak = pct_df[pct_df["peak_index"] == peak].sort_values("current_density")
        if df_peak.empty:
            continue
        x = df_peak["current_density"]
        pct_y = df_peak["pct_mean"]
        pct_err = np.maximum(df_peak["pct_std"].to_numpy(), 1.0)

        # Regular line + markers with error bars
        ax_pct.errorbar(
            x,
            pct_y,
            yerr=pct_err,
            marker=marker,
            linestyle="-",
            linewidth=1.5,
            color=color,
            ecolor=color,
            capsize=3,
            label=label,
        )

    ax_pct.set_ylabel("Percentage of total amplitude (%)")
    ax_pct.set_xlabel(r"Current density (A·cm$^{-2}$)")
    ax_pct.legend(frameon=legend_frameon)
    plt.tight_layout()
    plt.savefig("./results/fit_peak_params_percentages.png")
    plt.savefig("./results/fit_peak_params_percentages.svg", dpi=300)
    plt.close(fig_pct)

    # ------------------------------------------------------------------
    # 2) Figure: Stark slopes (cm⁻¹/V) of 4-HB water and 3-HB water
    # ------------------------------------------------------------------
    # Read current–voltage relation
    try:
        iv_df = pd.read_excel("./data/current vs voltage.xlsx")
        current_col = iv_df.columns[0]
        voltage_col = iv_df.columns[1]
        iv_df = iv_df.rename(columns={current_col: "current_A", voltage_col: "cell_voltage"})
    except FileNotFoundError:
        iv_df = None

    intervals_mA = [(50.0, 200.0), (200.0, 400.0), (400.0, 750.0)]
    interval_labels = ["0.05–0.2", "0.2–0.4", "0.4–0.75"]  # current density in A·cm⁻²

    def pos_at(current_mA, peak_index):
        row = agg[(agg["current_mA"] == current_mA) & (agg["peak_index"] == peak_index)]
        if row.empty:
            return np.nan, np.nan
        return float(row["pos_mean"].iloc[0]), float(row["pos_std"].iloc[0])

    def voltage_at(current_mA):
        if iv_df is None:
            return np.nan
        current_A = current_mA / 1000.0
        row = iv_df[iv_df["current_A"] == current_A]
        if row.empty:
            return np.nan
        return float(row["cell_voltage"].iloc[0])

    slopes_3hb = []
    slopes_4hb = []
    err_3hb = []
    err_4hb = []
    for c_low, c_high in intervals_mA:
        pos_3_low, std_3_low = pos_at(c_low, 3)
        pos_3_high, std_3_high = pos_at(c_high, 3)
        pos_4_low, std_4_low = pos_at(c_low, 2)
        pos_4_high, std_4_high = pos_at(c_high, 2)

        v_low = voltage_at(c_low)
        v_high = voltage_at(c_high)
        dv = v_high - v_low if not (np.isnan(v_low) or np.isnan(v_high)) else np.nan

        # 3-HB Stark slope and error
        if not np.isnan(pos_3_low) and not np.isnan(pos_3_high) and not np.isnan(dv) and dv != 0:
            dpos_3 = pos_3_high - pos_3_low
            slopes_3hb.append(dpos_3 / dv)
            sigma_dpos_3 = np.sqrt(std_3_low**2 + std_3_high**2)
            err_3hb.append(sigma_dpos_3 / abs(dv))
        else:
            slopes_3hb.append(np.nan)
            err_3hb.append(np.nan)

        # 4-HB Stark slope and error
        if not np.isnan(pos_4_low) and not np.isnan(pos_4_high) and not np.isnan(dv) and dv != 0:
            dpos_4 = pos_4_high - pos_4_low
            slopes_4hb.append(dpos_4 / dv)
            sigma_dpos_4 = np.sqrt(std_4_low**2 + std_4_high**2)
            err_4hb.append(sigma_dpos_4 / abs(dv))
        else:
            slopes_4hb.append(np.nan)
            err_4hb.append(np.nan)

    # Save Stark slope data (both species, all intervals)
    stark_rows = []
    for i, (c_low_high, label) in enumerate(zip(intervals_mA, interval_labels)):
        c_low_val, c_high_val = c_low_high  # (low_mA, high_mA)
        s3, e3 = slopes_3hb[i], err_3hb[i]
        s4, e4 = slopes_4hb[i], err_4hb[i]

        stark_rows.append(
            {
                "interval_mA_low": c_low_val,
                "interval_mA_high": c_high_val,
                "interval_label": label,
                "peak_index": 2,
                "species": label_peak_2,
                "stark_slope": s4,
                "stark_slope_err": e4,
            }
        )
        stark_rows.append(
            {
                "interval_mA_low": c_low_val,
                "interval_mA_high": c_high_val,
                "interval_label": label,
                "peak_index": 3,
                "species": label_peak_3,
                "stark_slope": s3,
                "stark_slope_err": e3,
            }
        )

    stark_df = pd.DataFrame(stark_rows)
    stark_df.to_csv("./results/fit_peak_params_stark_slopes_data.csv", index=False)

    x = np.arange(len(intervals_mA))
    width = 0.35

    # Two-panel figure for Stark analysis:
    # (a) 4-HB water percentage + Raman shift vs current density
    # (b) Stark slopes for 4-HB water and 3-HB water vs current-density interval
    fig_stark, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(8, 6), sharex=False)

    # Panel (a): 4-HB water percentage + Raman shift vs current density
    df_4hb_pct = pct_df[pct_df["peak_index"] == 2].sort_values("current_density")
    if not df_4hb_pct.empty:
        # Merge in Raman shift information for 4-HB (peak_index 2) from agg
        df_4hb_pos = (
            agg[agg["peak_index"] == 2][
                ["current_density", "pos_mean", "pos_std"]
            ]
            .drop_duplicates(subset="current_density")
        )
        df_4hb = df_4hb_pct.merge(
            df_4hb_pos, on="current_density", how="left", validate="one_to_one"
        )

        x_pct = df_4hb["current_density"]
        pct_y = df_4hb["pct_mean"]
        pct_err = np.maximum(df_4hb["pct_std"].to_numpy(), 1.0)
        if len(x_pct) > 1:
            dx = np.min(np.diff(np.unique(x_pct)))
            width_pct = dx * 0.4
        else:
            width_pct = 0.02
        dark_color_4 = tuple(0.6 * c for c in mcolors.to_rgb(color_peak_2))
        ax_top.bar(
            x_pct,
            pct_y,
            width=width_pct,
            yerr=pct_err,
            capsize=3,
            color=color_peak_2,
            ecolor=dark_color_4,
            alpha=0.7,
            label=label_peak_2,
        )
        ax_top.set_ylabel("4-HB water (%)")

        # Raman shift on right axis
        ax_top_right = ax_top.twinx()
        pos_y = df_4hb["pos_mean"]
        pos_err = df_4hb["pos_std"]
        ax_top_right.errorbar(
            x_pct,
            pos_y,
            yerr=pos_err,
            marker=marker,
            linestyle="-",
            linewidth=1.5,
            color=color_peak_2,
            ecolor="black",
            markerfacecolor="white",
            markeredgecolor="black",
            markeredgewidth=1.0,
        )
        ax_top_right.set_ylabel(r"Raman shift (cm$^{-1}$)")
        pos_fmt = ScalarFormatter(useMathText=False)
        pos_fmt.set_scientific(False)
        pos_fmt.set_useOffset(False)
        ax_top_right.yaxis.set_major_formatter(pos_fmt)

    ax_top.set_xticklabels([])

    # Panel (b): Stark slopes grouped bars
    err_4hb_plot = np.maximum(err_4hb, 0.5)
    err_3hb_plot = np.maximum(err_3hb, 0.5)

    ax_bottom.bar(
        x - width / 2,
        slopes_4hb,
        width,
        yerr=err_4hb_plot,
        capsize=4,
        color=color_peak_2,
        alpha=0.8,
        label=label_peak_2,
    )
    ax_bottom.bar(
        x + width / 2,
        slopes_3hb,
        width,
        yerr=err_3hb_plot,
        capsize=4,
        color=color_peak_3,
        alpha=0.8,
        label=label_peak_3,
    )

    ax_bottom.set_xticks(x)
    ax_bottom.set_xticklabels(interval_labels)
    ax_bottom.set_xlabel(r"Δ Current density (A·cm$^{-2}$)")
    ax_bottom.set_ylabel(r"Stark slope (cm$^{-1}$ V$^{-1}$)")
    ax_bottom.legend(frameon=legend_frameon)

    plt.tight_layout()
    plt.savefig("./results/fit_peak_params_stark_slopes.png")
    plt.savefig("./results/fit_peak_params_stark_slopes.svg", dpi=300)
    plt.close(fig_stark)

    # Restore previous global font setting
    if old_font is not None:
        plt.rcParams["font.family"] = old_font

    # ------------------------------------------------------------------
    # 3) Multipanel figures with individual fit plots (3x2 per page)
    # ------------------------------------------------------------------
    fit_files = sorted(
        glob.glob(os.path.join("results", "fit_current_*_exp_*.png"))
    )

    n_per_fig = 6
    n_rows, n_cols = 2, 3

    for fig_idx in range(0, len(fit_files), n_per_fig):
        chunk = fit_files[fig_idx : fig_idx + n_per_fig]
        if not chunk:
            continue

        fig, axes = plt.subplots(
            n_rows, n_cols, figsize=(12, 6), squeeze=True
        )

        for ax in axes.ravel():
            ax.axis("off")

        for ax, img_path in zip(axes.ravel(), chunk):
            img = plt.imread(img_path)
            ax.imshow(img)
            ax.axis("off")
            # Use file name (without extension) as panel label
            filename = os.path.splitext(os.path.basename(img_path))[0]
            current, exp = filename.split('_')[2], filename.split('_')[4]
            title = f'{current} / {exp}'
            # Title slightly inside the axes, closer to the plot
            ax.text(
                0.5,
                1.05,
                title,
                transform=ax.transAxes,
                ha="center",
                va="top",
                fontsize=10,
            )

        # Reduce space between panels and between panels and figure edges
        plt.subplots_adjust(
            left=0.03,
            right=0.97,
            top=0.97,
            bottom=0.03,
            wspace=0,   # even tighter horizontal space
            hspace=0,  # minimal vertical spacing between rows
        )
        out_idx = fig_idx // n_per_fig + 1
        out_path_png = f"./results/fit_current_multipanel_{out_idx}.png"
        out_path_svg = f"./results/fit_current_multipanel_{out_idx}.svg"
        plt.tight_layout()
        plt.savefig(out_path_png, dpi=300)
        plt.savefig(out_path_svg, dpi=300)
        plt.close(fig)

if __name__ == "__main__":
    plot_fit_params()