#!/usr/bin/env bash

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install mkdocs
python3 -m pip install mkdocs-material
python3 -m pip install mkdocs-glightbox
python3 -m pip install mkdocs-github-admonitions-plugin
