import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from water_analysis.pipeline import run_full_analysis_for_all_subfolders


if __name__ == "__main__":
    run_full_analysis_for_all_subfolders()