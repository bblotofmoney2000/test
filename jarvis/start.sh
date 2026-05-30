#!/bin/bash
# JARVIS — startup script

set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo ""
echo "  ██╗ █████╗ ██████╗ ██╗   ██╗██╗███████╗"
echo "  ██║██╔══██╗██╔══██╗╚██╗ ██╔╝██║██╔════╝"
echo "  ██║███████║██████╔╝ ╚████╔╝ ██║███████╗"
echo "  ██║██╔══██║██╔══██╗  ╚██╔╝  ██║╚════██║"
echo "  ██║██║  ██║██║  ██║   ██║   ██║███████║"
echo "  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚══════╝"
echo ""
echo "  Just A Rather Very Intelligent System"
echo "  ─────────────────────────────────────"
echo ""

# Create virtualenv if it doesn't exist
if [ ! -d "venv" ]; then
  echo "  [INIT] Creating Python virtual environment..."
  python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install / upgrade dependencies silently
echo "  [INIT] Verifying dependencies..."
pip install -q -r requirements.txt

echo "  [BOOT] Starting JARVIS on http://localhost:5000"
echo ""

# Open browser after a short delay (background)
(sleep 2 && xdg-open "http://localhost:5000" 2>/dev/null || true) &

python3 app.py
