#!/bin/zsh
# macOS double-click launcher. Normal mode saves only explicitly confirmed data.
app_dir="$(cd "$(dirname "$0")" && pwd)" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
  echo 'Plate Memory needs Python 3.10 or newer. Install Python, then open this file again.'
  read 'reply?Press Return to close.'
  exit 2
fi
exec python3 "$app_dir/plate-memory.py" "$@"
