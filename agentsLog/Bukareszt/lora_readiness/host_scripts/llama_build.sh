#!/bin/bash
set -u
R=/ephemeral/mm-lora; export UV_CACHE_DIR=$R/uv-cache UV_PYTHON_INSTALL_DIR=$R/uv-python
L=$R/src/llama.cpp
echo "$(date -u +%FT%TZ) tools venv"
$R/bin/uv venv --python 3.12 $R/venv-tools && $R/bin/uv pip install --python $R/venv-tools/bin/python cmake ninja
export PATH=$R/venv-tools/bin:$PATH
echo "$(date -u +%FT%TZ) convert venv"
( cd $L/requirements && $R/bin/uv venv --python 3.12 $R/venv-convert && $R/bin/uv pip install --python $R/venv-convert/bin/python -r requirements-convert_hf_to_gguf.txt --index-strategy unsafe-best-match && $R/bin/uv pip freeze --python $R/venv-convert/bin/python > $R/logs/convert_freeze.txt ) || echo FAIL_CONVERT_VENV
echo "$(date -u +%FT%TZ) cmake"
cmake -S $L -B $L/build -G Ninja -DGGML_CUDA=OFF -DLLAMA_CURL=OFF -DCMAKE_BUILD_TYPE=Release > $R/logs/cmake.log 2>&1 || echo FAIL_CMAKE
cmake --build $L/build --target llama-quantize -j 24 > $R/logs/build.log 2>&1 || echo FAIL_BUILD
ls -la $L/build/bin/
echo "$(date -u +%FT%TZ) LLAMA_DONE"
