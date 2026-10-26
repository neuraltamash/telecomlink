#!/usr/bin/env bash
set -euo pipefail
python -m pytest -q
npm run build
printf '\nAll checks completed.\n'
