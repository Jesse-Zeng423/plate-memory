#!/bin/sh
app_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Plate Memory needs Python 3.10 or newer.' >&2
  exit 2
fi
exec python3 "$app_dir/plate-memory.py" "$@"
