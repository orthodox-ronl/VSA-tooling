#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python -m pip install --upgrade pip

python -m pip install -e ".[rendering]"
python -m pip install pytest

python -c "import vsa; print('vsa OK:', vsa.__name__)"
