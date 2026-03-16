import pathlib

import tomli as toml


def get_project_root() -> pathlib.Path:
    """
    Return the project root directory.

    Assumes the package is located under ``src/water_analysis`` and walks
    up accordingly from this file.
    """
    return pathlib.Path(__file__).resolve().parents[2]


_CONFIG_PATH = get_project_root() / "config.toml"

with _CONFIG_PATH.open("rb") as f:
    config = toml.load(f)

