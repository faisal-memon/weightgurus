#!/usr/bin/env bash

set -u

# Add configurable random jitter before running the python script.
# Default is up to 300 seconds (5 minutes).
JITTER_MAX="${WG_JITTER_SECONDS_MAX:-300}"
if ! [[ "$JITTER_MAX" =~ ^[0-9]+$ ]]; then
  echo "Invalid WG_JITTER_SECONDS_MAX='$JITTER_MAX'. Falling back to 300."
  JITTER_MAX=300
fi

if [ "$JITTER_MAX" -gt 0 ]; then
  jitter=$((RANDOM % (JITTER_MAX + 1)))
  echo "Applying jitter: ${jitter}s"
  sleep "$jitter"
fi

# Run the python script
/usr/local/bin/python /app/main.py >> /proc/1/fd/1 2>&1
