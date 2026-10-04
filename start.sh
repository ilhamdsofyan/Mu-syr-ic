#!/usr/bin/env bash

# Get the directory where this script lives
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check venv exists
if [ ! -f "$DIR/.venv/bin/python" ]; then
    echo ""
    echo "  ╔══════════════════════════════════════════════════════╗"
    echo "  ║  Mu(syr)ic hasn't been installed yet!               ║"
    echo "  ║  Please run install.sh first, then try again.       ║"
    echo "  ╚══════════════════════════════════════════════════════╝"
    echo ""
    read -p "Press Enter to close..." _
    exit 1
fi

# Activate venv and launch interactive app
source "$DIR/.venv/bin/activate"
python -m musyric.app
