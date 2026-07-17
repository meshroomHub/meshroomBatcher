#!/usr/bin/env bash

DOCS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
PKG_ROOT_DIR=$( dirname "$DOCS_DIR" )

OUTPUT_FOLDER="$PKG_ROOT_DIR/output"

if [ -d "$OUTPUT_FOLDER" ]; then rm -Rf "$OUTPUT_FOLDER"; fi

source $PKG_ROOT_DIR/.venv/bin/activate

# Build the doc
python3 -m mkdocs build --config-file "$DOCS_DIR/mkdocs.yml" --site-dir "$OUTPUT_FOLDER/html"
