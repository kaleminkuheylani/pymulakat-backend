#!/bin/bash
# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Ensure log file exists or create it
mkdir -p data
touch data/cron.log

# Log start time
echo "" >> data/cron.log
echo "=== Cron Job Started: $(date) ===" >> data/cron.log

# Check if uv is installed, otherwise use virtualenv python
if command -v uv &> /dev/null; then
    echo "Running with uv..." >> data/cron.log
    uv run python services/gemini.py --generate-creative --count 1 --email kaleminkuheylani@gmail.com >> data/cron.log 2>&1
elif [ -f ".venv/bin/python" ]; then
    echo "Running with .venv/bin/python..." >> data/cron.log
    .venv/bin/python services/gemini.py --generate-creative --count 1 --email kaleminkuheylani@gmail.com >> data/cron.log 2>&1
else
    echo "Running with system python..." >> data/cron.log
    python services/gemini.py --generate-creative --count 1 --email kaleminkuheylani@gmail.com >> data/cron.log 2>&1
fi

echo "=== Cron Job Finished: $(date) ===" >> data/cron.log
