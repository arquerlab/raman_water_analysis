import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from water_analysis.io import read_long_dataframe
from water_analysis.fitting import fit_currents
from water_analysis.plotting import plot_fit_params


def main() -> None:
    long_df = read_long_dataframe()
    fit_results = fit_currents(long_df, bs_method="integrated", plot=False)
    plot_fit_params(fit_results)


if __name__ == "__main__":
    main()

