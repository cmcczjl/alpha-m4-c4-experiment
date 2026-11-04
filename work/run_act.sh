#!/usr/bin/env bash
set -e

# -------------------------------------------------
# 1. Ensure `act` is available
# -------------------------------------------------
if ! command -v act >/dev/null 2>&1; then
    echo "[INFO] `act` not found, attempting installation via pip..."
    # Try installing with pip; fallback to pip3 if needed
    if command -v pip >/dev/null 2>&1; then
        pip install act
    elif command -v pip3 >/dev/null 2>&1; then
        pip3 install act
    else
        echo "[ERROR] Neither pip nor pip3 is available. Cannot install act."
        exit 1
    fi
fi

# Verify installation
echo "[INFO] Verifying `act` installation:"
act --version

# -------------------------------------------------
# 2. Prepare the target script `install_and_test_act.sh`
# -------------------------------------------------
TARGET_SCRIPT="work/install_and_test_act.sh"

if [ -f "$TARGET_SCRIPT" ]; then
    # Prepend `set -x` if it's not already the first non‑shebang line
    first_line=$(head -n1 "$TARGET_SCRIPT")
    if [[ "$first_line" != "set -x"* && "$first_line" != "#!"* ]]; then
        sed -i '1i set -x' "$TARGET_SCRIPT"
    elif [[ "$first_line" == "#!"* ]]; then
        second_line=$(sed -n '2p' "$TARGET_SCRIPT")
        if [[ "$second_line" != "set -x"* ]]; then
            sed -i '2i set -x' "$TARGET_SCRIPT"
        fi
    fi
else
    # If the script does not exist, create a minimal placeholder
    echo "#!/usr/bin/env bash" > "$TARGET_SCRIPT"
    echo "set -x" >> "$TARGET_SCRIPT"
    echo "echo \"Placeholder: no original install_and_test_act.sh found.\"" >> "$TARGET_SCRIPT"
fi

chmod +x "$TARGET_SCRIPT"

# -------------------------------------------------
# 3. Execute the script and capture full log
# -------------------------------------------------
LOG_FILE="act_run.log"
echo "[INFO] Executing $TARGET_SCRIPT, logging to $LOG_FILE ..."
bash "$TARGET_SCRIPT" > "$LOG_FILE" 2>&1
echo "[INFO] Execution finished. Log saved to $LOG_FILE."