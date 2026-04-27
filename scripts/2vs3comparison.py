from pathlib import Path
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

folder_2p = Path("results_2peaks")
folder_3p = Path("results")
fits_filename = "fit_peak_params_agg.csv"
percentages_filename = "fit_peak_params_percentages_data.csv"
folders = [folder_2p, folder_3p]
subfolder = "Ar"

capsize = 3
marker = "o"
colors = {1: "#9467BDFF", 2: "#1F77B4FF", 3: "#2CA02CFF", 4: "#8C564B55"}
labels = {1: "Membrane", 2: "4-HB water", 3: "3-HB water", 4: "0-HB water"}
legend_frameon = False

n_cols = 3
n_rows = 3
fig, ax = plt.subplots(n_rows, n_cols, figsize=(20, 10), sharex=False)
fig2, ax2 = plt.subplots(1, 1, figsize=(8, 6))
for folder, label, line_style in zip(folders, ["2p", "3p"], ["-", "--"]):
    df = pd.read_csv(folder / subfolder / fits_filename)
    print(df["peak_index"].unique())
    df_percentages = pd.read_csv(folder / subfolder / percentages_filename)
    if 1 in df["peak_index"].unique():
        df = df[df["peak_index"] != 1]
        df_percentages = df_percentages[df_percentages["peak_index"] != 1]
    n_peaks_here = len(df["peak_index"].unique())
    for i, peak in zip(range(n_peaks_here), df["peak_index"].unique()):
        df_peak = df[df["peak_index"] == peak]
        df_peak_percentages = df_percentages[df_percentages["peak_index"] == peak]
        for j, column in enumerate(df_peak.columns[-7:-1:2]):
            ax[i, j].errorbar(
                df_peak["current_mA"],
                df_peak[column],
                yerr=df_peak[column.split("_")[0] + "_std"],
                label=f"{labels[peak]} (n={n_peaks_here})",
                marker=marker,
                capsize=capsize,
                elinewidth=1.5,
                color=colors[peak],
                linestyle=line_style,
            )
            ax[i, j].legend(frameon=legend_frameon)
            ax[i, j].set_title(f"{column.split("_")[0]} {labels[peak]}")
            ax[i, j].set_xlabel("Current (mA)")
            ax[i, j].set_ylabel(column.split("_")[0])
        ax2.errorbar(
            df_peak_percentages["current_density"],
            df_peak_percentages["pct_mean"],
            yerr=df_peak_percentages["pct_std"],
            label=f"{labels[peak]} (n={n_peaks_here})",
            marker=marker,
            capsize=capsize,
            elinewidth=1.5,
            color=colors[peak],
            linestyle=line_style,
        )
        ax2.legend(frameon=legend_frameon)
        ax2.set_xlabel("Current density (A/cm²)")
        ax2.set_ylabel("Percentage of total amplitude (%)")
        ax2.set_title(f"{labels[peak]}")
fig.tight_layout()
fig2.tight_layout()
os.makedirs("2vs3_comparison", exist_ok=True)
os.makedirs(f"2vs3_comparison/{subfolder}", exist_ok=True)
fig.savefig(f"2vs3_comparison/{subfolder}/fit_params_comparison_2vs3.png")
fig.savefig(f"2vs3_comparison/{subfolder}/fit_params_comparison_2vs3.svg")
fig2.savefig(f"2vs3_comparison/{subfolder}/fit_params_comparison_2vs3_percentages.png")
fig2.savefig(f"2vs3_comparison/{subfolder}/fit_params_comparison_2vs3_percentages.svg")
plt.close(fig)
plt.close(fig2)

# Dumbbell plots: 2p vs 3p for each peak and parameter, by current.
df_2p = pd.read_csv(folder_2p / subfolder / fits_filename)
df_3p = pd.read_csv(folder_3p / subfolder / fits_filename)

if 1 in df_2p["peak_index"].unique():
    df_2p = df_2p[df_2p["peak_index"] != 1]
if 1 in df_3p["peak_index"].unique():
    df_3p = df_3p[df_3p["peak_index"] != 1]

params = [
    ("amp_mean", "Amplitude (mean)"),
    ("fwhm_mean", "FWHM (mean)"),
    ("pos_mean", "Position (mean)"),
]

peaks = sorted(set(df_2p["peak_index"].unique()).intersection(set(df_3p["peak_index"].unique())))

fig_db, ax_db = plt.subplots(
    nrows=len(peaks),
    ncols=len(params),
    figsize=(18, 4.5 * max(1, len(peaks))),
    sharey="row",
)
if len(peaks) == 1:
    ax_db = np.array([ax_db])

for r, peak in enumerate(peaks):
    a = df_2p[df_2p["peak_index"] == peak][["current_mA"] + [p[0] for p in params]].copy()
    b = df_3p[df_3p["peak_index"] == peak][["current_mA"] + [p[0] for p in params]].copy()
    m = a.merge(b, on="current_mA", suffixes=("_2p", "_3p"), how="inner").sort_values("current_mA")
    y = m["current_mA"].to_numpy()

    for c, (col, title) in enumerate(params):
        axc = ax_db[r, c]
        x2 = m[f"{col}_2p"].to_numpy()
        x3 = m[f"{col}_3p"].to_numpy()

        # connecting segments
        for yi, xa, xb in zip(y, x2, x3):
            axc.plot([xa, xb], [yi, yi], color="0.6", linewidth=2, zorder=1)

        axc.scatter(x2, y, color="black", s=30, label="2p" if (r == 0 and c == 0) else None, zorder=2)
        axc.scatter(x3, y, color="tab:red", s=30, label="3p" if (r == 0 and c == 0) else None, zorder=3)

        if r == 0:
            axc.set_title(title, fontsize=12)
        if c == 0:
            axc.set_ylabel("Current (mA)")
        axc.grid(True, axis="x", alpha=0.2)

    # annotate peak label on the left-most subplot row
    ax_db[r, 0].text(
        0.01,
        0.98,
        labels.get(peak, f"Peak {peak}"),
        transform=ax_db[r, 0].transAxes,
        ha="left",
        va="top",
        fontsize=12,
        fontweight="bold",
    )

fig_db.legend(frameon=False, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 0.98))
fig_db.tight_layout(rect=(0, 0, 1, 0.96))
fig_db.savefig(f"2vs3_comparison/{subfolder}/dumbbell_2p_vs_3p.png", dpi=300)
fig_db.savefig(f"2vs3_comparison/{subfolder}/dumbbell_2p_vs_3p.svg")
plt.close(fig_db)


def load_manifest(results_root: Path, dataset: str) -> dict[tuple[str, str], Path]:
    manifest_path = results_root / dataset / "fit_traces_manifest.json"
    with manifest_path.open("r", encoding="utf-8") as f:
        items = json.load(f)
    out: dict[tuple[str, str], Path] = {}
    for it in items:
        key = (str(it["sample"]), str(it["experiment"]))
        rel = str(it["npz"])
        out[key] = (results_root / dataset / rel).resolve()
    return out


def try_load_npz(path: Path) -> dict | None:
    if not path.exists():
        print(f"Missing npz: {path}")
        return None
    with np.load(path, allow_pickle=False) as z:
        d = {k: z[k] for k in z.files}
    # Normalize string scalars if present
    for k in ("sample", "experiment"):
        if k in d and np.ndim(d[k]) == 0:
            try:
                d[k] = str(d[k].item())
            except Exception:
                d[k] = str(d[k])
    return d


def gaussian_components(d: dict) -> list[tuple[str, np.ndarray]]:
    """
    Return [(peak_name, gaussian)], where gaussian is the *standalone* Gaussian (no baseline).
    Uses the same triplet encoding as the fitting code: (pos, amp, fwhm) repeated.
    """
    wn = d["wn"]
    popt = d["popt"]
    start_params = len(popt) % 3
    names = [str(n).lower() for n in d.get("peak_names", [])]
    out: list[tuple[str, np.ndarray]] = []
    comp_idx = 0
    for peak_idx in range(start_params, len(popt) - start_params, 3):
        pos, amp, fwhm = popt[peak_idx : peak_idx + 3]
        g = amp * np.exp(-(np.power(wn - pos, 2) / (fwhm * fwhm / 4.0 / np.log(2.0))))
        name = names[comp_idx] if comp_idx < len(names) else f"gaussian_{comp_idx+1}"
        out.append((name, g))
        comp_idx += 1
    return out


# Overlay + delta residuals plots
man_2p = load_manifest(folder_2p, subfolder)
man_3p = load_manifest(folder_3p, subfolder)
keys = sorted(set(man_2p.keys()).intersection(set(man_3p.keys())), key=lambda k: float(k[0].split()[0]))

n_per_fig = 6
for fig_idx in range(0, len(keys), n_per_fig):
    chunk_keys = keys[fig_idx : fig_idx + n_per_fig]
    if not chunk_keys:
        continue

    fig_ov = plt.figure(figsize=(24, 12), constrained_layout=False)
    outer = fig_ov.add_gridspec(nrows=2, ncols=3, wspace=0.18, hspace=0.25)

    axes_top = []
    axes_bot = []
    shared_x = None
    for r in range(2):
        for c in range(3):
            inner = outer[r, c].subgridspec(nrows=2, ncols=1, height_ratios=[65, 35], hspace=0.05)
            ax_t = fig_ov.add_subplot(inner[0], sharex=shared_x) if shared_x is not None else fig_ov.add_subplot(inner[0])
            if shared_x is None:
                shared_x = ax_t
            ax_b = fig_ov.add_subplot(inner[1], sharex=shared_x)
            axes_top.append(ax_t)
            axes_bot.append(ax_b)

    for ax in axes_top + axes_bot:
        ax.set_visible(False)

    for k_idx, (sample, exp) in enumerate(chunk_keys):
        ax_t = axes_top[k_idx]
        ax_b = axes_bot[k_idx]
        d2 = try_load_npz(man_2p[(sample, exp)])
        d3 = try_load_npz(man_3p[(sample, exp)])
        if d2 is None or d3 is None:
            continue

        wn = d2["wn"]
        ax_t.set_visible(True)
        ax_b.set_visible(True)

        ax_t.plot(wn, d2["intensity"], color="black", linewidth=1.0, label="Data")
        ax_t.plot(wn, d2["fit_total"], color="tab:blue", linewidth=1.2, label="Fit 2p")
        ax_t.plot(wn, d3["fit_total"], color="tab:red", linewidth=1.2, label="Fit 3p")

        # Optional baselines (helpful when baseline differs)
        if "baseline" in d2:
            ax_t.plot(wn, d2["baseline"], color="tab:blue", linestyle="--", linewidth=1.0, alpha=0.8, label="Baseline 2p")
        if "baseline" in d3:
            ax_t.plot(wn, d3["baseline"], color="tab:red", linestyle="--", linewidth=1.0, alpha=0.8, label="Baseline 3p")

        # Gaussian components (colored by peak name, linestyle by model)
        peak_color = {"membrane": "#8C564B", "4hb": "#2CA02C", "3hb": "#1F77B4", "0hb": "#9467BD"}
        for name, g in gaussian_components(d2):
            base = d2.get("baseline", 0.0)
            ax_t.plot(wn, base + g, color=peak_color.get(name, "0.5"), alpha=0.35, linewidth=1.0, linestyle="-")
        for name, g in gaussian_components(d3):
            base = d3.get("baseline", 0.0)
            ax_t.plot(wn, base + g, color=peak_color.get(name, "0.5"), alpha=0.35, linewidth=1.0, linestyle="--")

        delta_res = d3["residuals"] - d2["residuals"]
        ax_b.axhline(0, color="0.7", linewidth=1.0)
        ax_b.plot(wn, d2["residuals"], color="tab:blue", alpha=0.35, linewidth=1.0, label="Residuals 2p")
        ax_b.plot(wn, d3["residuals"], color="tab:red", alpha=0.35, linewidth=1.0, label="Residuals 3p")
        ax_b.plot(wn, delta_res, color="purple", linewidth=1.2, label="ΔResiduals (3p-2p)")

        ax_t.text(0.98, 0.98, f"{sample} / {exp}", transform=ax_t.transAxes, ha="right", va="top", fontsize=14)

        # Labels: x only bottom row, y only left column
        rr = k_idx // 3
        cc = k_idx % 3
        if rr == 1:
            ax_b.set_xlabel("Raman shift (cm$^{-1}$)", fontsize=14)
        else:
            ax_b.tick_params(labelbottom=False)
            ax_t.xaxis.tick_top()
            ax_t.tick_params(labeltop=True, top=True, labelbottom=False, bottom=False)
            ax_t.set_xlabel("Raman shift (cm$^{-1}$)", fontsize=14)
            ax_t.xaxis.set_label_position("top")

        if cc == 0:
            ax_t.set_ylabel("Intensity (a.u.)", fontsize=14)
            ax_b.set_ylabel("ΔResiduals", fontsize=14)

    # Shared legend from first visible panel
    first_vis = next((i for i, ax in enumerate(axes_top) if ax.get_visible()), None)
    if first_vis is not None:
        h1, l1 = axes_top[first_vis].get_legend_handles_labels()
        h2, l2 = axes_bot[first_vis].get_legend_handles_labels()
        fig_ov.legend(h1 + h2, l1 + l2, frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 0.995))

    fig_ov.subplots_adjust(left=0.06, right=0.99, top=0.86, bottom=0.08)
    out_idx = fig_idx // n_per_fig + 1
    fig_ov.savefig(f"2vs3_comparison/{subfolder}/overlay_deltaResiduals_{out_idx}.png", dpi=200)
    fig_ov.savefig(f"2vs3_comparison/{subfolder}/overlay_deltaResiduals_{out_idx}.svg", dpi=200)
    plt.close(fig_ov)