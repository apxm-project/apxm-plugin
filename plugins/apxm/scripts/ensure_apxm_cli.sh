#!/usr/bin/env bash
set -euo pipefail

if ! command -v dekk >/dev/null 2>&1; then
  echo "dekk is not on PATH. Install or activate APXM/Dekk before running APXM workflows." >&2
  exit 2
fi

if ! dekk apxm doctor; then
  echo "dekk apxm doctor failed. Run APXM setup for this environment before executing workflows." >&2
  exit 3
fi

