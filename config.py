import tomli as toml

with open('config.toml', 'rb') as f:
    config = toml.load(f)