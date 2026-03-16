from __future__ import annotations

import pathlib
from typing import Optional

import pandas as pd
import numpy as np

from .config import config


def get_project_root() -> pathlib.Path:
    """
    Return the project root directory.

    This assumes the package is located under ``src/water_analysis`` and
    walks up accordingly from the current file.
    """
    return pathlib.Path(__file__).resolve().parents[2]


def default_data_dir() -> pathlib.Path:
    """Return the default data directory path."""
    return get_project_root() / "data"


def default_results_dir() -> pathlib.Path:
    """Return the default results directory path."""
    return get_project_root() / "results"


def read_long_dataframe(
    excel_path: Optional[pathlib.Path] = None,
    current_voltage_excel: Optional[pathlib.Path] = None,
) -> pd.DataFrame:
    """
    Read the spectroscopy Excel file and return a tidy long-form dataframe.

    Parameters
    ----------
    excel_path:
        Optional explicit path to the main spectroscopy Excel file.
        If omitted, ``config['data_path']`` is used, interpreted relative
        to the project root when the path is not absolute.
    current_voltage_excel:
        Optional explicit path to the current–voltage Excel file.
        If omitted, ``data/current vs voltage.xlsx`` relative to the
        project root is used.
    """
    root = get_project_root()

    if excel_path is None:
        configured = pathlib.Path(config["data_path"])
        excel_path = configured if configured.is_absolute() else root / configured

    if current_voltage_excel is None:
        current_voltage_excel = root / "data" / "current vs voltage.xlsx"

    tabs = pd.read_excel(excel_path, header=None, sheet_name=None)

    long_dfs = []

    for tab_name, df in tabs.items():
        if tab_name == "4 mA":
            continue

        for i in range(1, len(df.columns), 2):
            wn = df[i - 1]
            currents = df[i]
            if wn.iloc[0] < 3000:
                continue
            long_dfs.append(
                pd.DataFrame(
                    {
                        "sample": tab_name,
                        "experiment": f"exp{i // 2 + 1}",
                        "wn": wn,
                        "int": currents,
                    }
                )
            )

    long_df = pd.concat(long_dfs, ignore_index=True)

    try:
        iv_df = pd.read_excel(current_voltage_excel)
        current_col = iv_df.columns[0]
        voltage_col = iv_df.columns[1]
        iv_df = iv_df.rename(columns={current_col: "current_A", voltage_col: "cell_voltage"})

        long_df["current_A"] = long_df["sample"].str.split().str[0].astype(float) / 1000.0
        long_df = long_df.merge(iv_df, how="left", on="current_A")
    except FileNotFoundError:
        # If the IV file is missing, keep the long_df without extra columns.
        pass

    out_path = root / "data" / "long_df.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    long_df.to_csv(out_path, index=False)

    return long_df

def nearest_intensity(target, wn, int_corr):
    idx = np.argmin(np.abs(wn - target))
    return float(int_corr[idx])