from __future__ import annotations

import pathlib
from typing import Optional

from .config import config
from .fitting import fit_currents
from .io import get_project_root, read_long_dataframe
from .plotting import plot_fit_params


def run_full_analysis_for_all_subfolders(
    data_root: Optional[pathlib.Path] = None,
    results_root: Optional[pathlib.Path] = None,
    bs_method: str = "integrated",
    plot_fitting: bool = False,
) -> None:
    """
    Run the full Raman analysis pipeline for each input dataset subfolder.

    Discovery strategy:
    - Find all Excel files under ``data_root`` recursively whose name contains
      ``"_data"`` (e.g. ``Ar_data.xlsx`` or ``CO2_data.xlsx``).
    - For each match, treat its parent folder as a single "dataset subfolder".
    - Use ``current vs voltage.xlsx`` from the same subfolder if present,
      otherwise fall back to ``<data_root>/current vs voltage.xlsx``.
    - Write outputs to ``<results_root>/<dataset_subfolder_relative_path>/``.
    """

    project_root = get_project_root()
    data_root = data_root if data_root is not None else project_root / "data"
    results_root = results_root if results_root is not None else project_root / "results"

    current_voltage_basename = "current vs voltage.xlsx"

    # Primary discovery: any spreadsheet with "_data" in its filename.
    input_excels = sorted(
        [p for p in data_root.rglob("*.xlsx") if "_data" in p.name.lower()]
        + [p for p in data_root.rglob("*.xls") if "_data" in p.name.lower()]
    )

    # Backward-compatible fallback: if nothing is found under data_root,
    # analyze the file pointed by config["data_path"] as a single dataset.
    if not input_excels:
        configured = pathlib.Path(config["data_path"])
        excel_path = configured if configured.is_absolute() else project_root / configured
        input_excels = [excel_path]

    for excel_path in input_excels:
        # Treat the directory containing the spectroscopy Excel as the dataset folder.
        dataset_dir = excel_path.parent
        rel_dataset_dir = dataset_dir.relative_to(data_root) if dataset_dir.is_relative_to(data_root) else dataset_dir.name

        run_results_dir = results_root / rel_dataset_dir
        run_results_dir.mkdir(parents=True, exist_ok=True)

        candidate_iv = dataset_dir / current_voltage_basename
        iv_path = candidate_iv if candidate_iv.exists() else data_root / current_voltage_basename

        print(f"Processing dataset: {dataset_dir}")
        print(f"  Input Excel: {excel_path.name}")
        print(f"  IV Excel: {iv_path}")
        print(f"  Results: {run_results_dir}")

        long_df_out_path = run_results_dir / "long_df.csv"

        long_df = read_long_dataframe(
            excel_path=excel_path,
            current_voltage_excel=iv_path,
            long_df_out_path=long_df_out_path,
        )

        fit_results = fit_currents(
            long_df=long_df,
            bs_method=bs_method,
            plot=plot_fitting,
            results_dir=str(run_results_dir),
        )

        plot_fit_params(
            fit_results=fit_results,
            results_dir=str(run_results_dir),
            current_voltage_excel=iv_path,
        )

