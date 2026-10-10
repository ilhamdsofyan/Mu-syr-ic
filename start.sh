#!/usr/bin/env bash

# Get the directory where this script lives
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check venv exists
if [ ! -f "$DIR/.venv/bin/python" ]; then
    echo ""
    echo "  ========================================================"
    echo "    Mu(syr)ic is not installed yet!"
    echo "    Please run install.sh first, then try again."
    echo "  ========================================================"
    echo ""
    read -p "Press Enter to close..." _
    exit 1
fi

# Activate venv and launch interactive app (or CLI if args provided)
source "$DIR/.venv/bin/activate"
if [ $# -eq 0 ]; then
    python -m musyric.app
else
    python -m musyric.cli "$@"
fi
