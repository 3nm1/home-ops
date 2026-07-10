#!/bin/sh
set -eu

: "${TP_HOSTNAME:?TP_HOSTNAME is required}"
: "${TP_THEME:=hotpink}"

base="https://${TP_HOSTNAME}"
sheets="<link rel='stylesheet' href='${base}/css/base/sabnzbd/sabnzbd-base.css'>"
sheets="${sheets} <link rel='stylesheet' href='${base}/css/theme-options/${TP_THEME}.css'>"

if [ ! -d /app/interfaces ]; then
  echo "ERROR: /app/interfaces not found in image" >&2
  exit 1
fi

mkdir -p /ui
cp -a /app/interfaces/. /ui/

for file in \
  /ui/Glitter/templates/main.tmpl \
  /ui/Config/templates/_inc_header_uc.tmpl \
  /ui/Config/templates/login/main.tmpl \
  /ui/wizard/inc_top.tmpl
do
  if [ -f "$file" ] && ! grep -q "${TP_HOSTNAME}/css/base" "$file"; then
    sed -i "s|</head>|${sheets}</head>|g" "$file"
  fi
done
