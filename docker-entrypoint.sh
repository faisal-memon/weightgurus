#!/usr/bin/env bash

set -euo pipefail

WG_UPDATE_INTERVAL="${WG_UPDATE_INTERVAL:-24h}"
if [[ ! "$WG_UPDATE_INTERVAL" =~ ^[0-9]+[mh]?$ ]]; then
  echo "Invalid WG_UPDATE_INTERVAL='$WG_UPDATE_INTERVAL', expected format '[0-9]+[mh]?'"
  exit 1
fi

case "$WG_UPDATE_INTERVAL" in
  *h)
    HOURS="${WG_UPDATE_INTERVAL%h}"
    if (( HOURS < 1 || HOURS > 24 )); then
      echo "WG_UPDATE_INTERVAL hours value must be between 1 and 24"
      exit 1
    fi
    MINUTES="0"
    HOURS="*/${HOURS}"
    ;;
  *)
    MINUTES="${WG_UPDATE_INTERVAL%m}"
    if (( MINUTES < 1 || MINUTES > 60 )); then
      echo "WG_UPDATE_INTERVAL minutes value must be between 1 and 60"
      exit 1
    fi
    MINUTES="*/${MINUTES}"
    HOURS="*"
    ;;
esac

sed "s|\${MINUTES} \${HOURS}|${MINUTES} ${HOURS}|g" \
  < /defaults/weightgurus-cron.tmpl \
  > /etc/cron.d/weightgurus-cron

chmod 0644 /etc/cron.d/weightgurus-cron
printenv > /etc/environment

echo "WG_UPDATE_INTERVAL=${WG_UPDATE_INTERVAL}"
echo "Cron schedule: $(awk 'NF && $1 !~ /^#/ {print $1, $2, $3, $4, $5; exit}' /etc/cron.d/weightgurus-cron)"

exec cron -f
