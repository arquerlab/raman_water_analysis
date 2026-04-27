import pathlib
import sys
import argparse

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from water_analysis.plotting import plot_fit_params


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate summary plots from an existing fit_peak_params.csv.")
    parser.add_argument(
        "--subfolder",
        type=str,
        default=None,
        help="If provided, read/write results under results/<subfolder>/ (e.g. flow_cell).",
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default=None,
        help="Optional explicit results directory containing fit_peak_params.csv (overrides --subfolder).",
    )
    args = parser.parse_args()

    results_dir = args.results_dir
    if results_dir is None and args.subfolder:
        normalized = args.subfolder.replace("\\", "/").strip("/")
        results_dir = str(PROJECT_ROOT / "results" / pathlib.Path(normalized))

    plot_fit_params(results_dir=results_dir)


if __name__ == "__main__":
    main()

