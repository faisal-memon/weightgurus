#!/usr/bin/env bash
chmod +x /app/run_with_jitter.sh
# Add a small random jitter (up to 30 minutes) before running the python script
jitter=$((RANDOM % 1800))
# Sleep for jitter seconds
sleep $jitter
# Run the python script
python /app/main.py >> /var/log/python.log 2>&1
