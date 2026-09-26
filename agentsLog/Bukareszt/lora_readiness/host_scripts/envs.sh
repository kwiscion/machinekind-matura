#!/bin/bash
# usage: envs.sh cpu|gpu   (archives must be fetched by fetch_src.sh first)
set -u
R=/ephemeral/mm-lora; K=$1; V=$R/venv-$K
export UV_CACHE_DIR=$R/uv-cache UV_PYTHON_INSTALL_DIR=$R/uv-python
echo "$(date -u +%FT%TZ) venv $K"
$R/bin/uv venv --clear --python 3.12 $V || { echo FAIL_VENV; exit 1; }
if [ $K = cpu ]; then IDX=https://download.pytorch.org/whl/cpu; TV=torch==2.8.0+cpu; else IDX=https://download.pytorch.org/whl/cu128; TV=torch==2.8.0; fi
echo "$(date -u +%FT%TZ) torch $TV"
$R/bin/uv pip install --python $V/bin/python "$TV" --index-url $IDX || echo FAIL_TORCH
echo "$(date -u +%FT%TZ) transformers/peft from exact-commit archives"
$R/bin/uv pip install --python $V/bin/python "transformers @ file://$R/src/transformers-96331a9f.zip" "peft @ file://$R/src/peft-b8674c86.zip" "torch==2.8.0" jinja2 sentencepiece protobuf || echo FAIL_TFPEFT
$R/bin/uv pip freeze --python $V/bin/python > $R/logs/${K}_freeze.txt
echo "$(date -u +%FT%TZ) ENV_DONE $K"
