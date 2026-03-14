#!/bin/bash
# NeuroRift Global Wrapper Script
# Designed and developed by demonking369

# Absolute path to the main script
MAIN_SCRIPT="/home/arun/tools/Custom_T_1/VulnForge/neurorift_main.py"

if [ ! -f "$MAIN_SCRIPT" ]; then
    echo "❌ Error: Could not find neurorift_main.py at $MAIN_SCRIPT"
    exit 1
fi

# Activate virtual environment if it exists
if [ -f "/home/arun/tools/Custom_T_1/VulnForge/.venv/bin/activate" ]; then
    source "/home/arun/tools/Custom_T_1/VulnForge/.venv/bin/activate"
fi

# Run the script
exec python3 "$MAIN_SCRIPT" "$@"
