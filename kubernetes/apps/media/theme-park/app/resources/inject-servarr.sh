#!/bin/sh
set -eu

: "${TP_APP:?TP_APP is required}"
: "${TP_HOSTNAME:?TP_HOSTNAME is required}"
: "${TP_THEME:=hotpink}"

base="https://${TP_HOSTNAME}"
sheets="<link rel='stylesheet' href='${base}/css/base/${TP_APP}/${TP_APP}-base.css'>"
sheets="${sheets} <link rel='stylesheet' href='${base}/css/theme-options/${TP_THEME}.css'>"

if [ -n "${TP_ADDON:-}" ]; then
  for addon in $(echo "$TP_ADDON" | tr "|" " "); do
    sheets="${sheets} <link rel='stylesheet' href='${base}/css/addons/${TP_APP}/${addon}/${addon}.css'>"
  done
fi

if [ ! -d /app/bin/UI ]; then
  echo "ERROR: /app/bin/UI not found in image" >&2
  exit 1
fi

mkdir -p /ui
cp -a /app/bin/UI/. /ui/

for file in /ui/index.html /ui/login.html; do
  if [ -f "$file" ] && ! grep -q "${TP_HOSTNAME}/css/base" "$file"; then
    sed -i "s|</body>|${sheets}</body>|g" "$file"
  fi
done
