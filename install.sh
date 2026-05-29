#!/bin/bash
# mug install script — creates a system-wide 'mug' command via symlink

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="/usr/local/bin/mug"

# Verify Python 3 is available
if ! command -v python3 &>/dev/null; then
    echo "[!] python3 not found. Install it first: sudo apt install python3"
    exit 1
fi

# Make the script executable
chmod +x "$SCRIPT_DIR/mug.py"

# Create symlink (symlink means git pull updates the command automatically)
if [ -L "$TARGET" ] || [ -f "$TARGET" ]; then
    echo "[*] Removing existing $TARGET"
    sudo rm -f "$TARGET"
fi

sudo ln -s "$SCRIPT_DIR/mug.py" "$TARGET"

echo "[+] Installed:  mug -> $TARGET"
echo "[+] Try it:     mug -i"
echo "[+] Or:         mug --help"
