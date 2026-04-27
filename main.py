import pathlib
import sys
import argparse

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from water_analysis.pipeline import run_full_analysis_for_all_subfolders


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full Raman analysis pipeline.")
    parser.add_argument(
        "--subfolder",
        type=str,
        default=None,
        help="Only process datasets whose relative folder under data/ starts with this value (e.g. flow_cell).",
    )
    args = parser.parse_args()

    run_full_analysis_for_all_subfolders(only_subfolder=args.subfolder)


if __name__ == "__main__":
    main()