#!/bin/sh
set -eu

: "${TP_HOSTNAME:?TP_HOSTNAME is required}"
: "${TP_THEME:=hotpink}"

base="https://${TP_HOSTNAME}"
sheets="<link rel='stylesheet' href='${base}/css/base/sabnzbd/sabnzbd-base.css'>"
sheets="${sheets} <link rel='stylesheet' href='${base}/css/theme-options/${TP_THEME}.css'>"

mkdir -p /ui
cp -a /app/. /ui/

for file in \
  /ui/interfaces/Glitter/templates/main.tmpl \
  /ui/interfaces/Config/templates/_inc_header_uc.tmpl \
  /ui/interfaces/Config/templates/login/main.tmpl \
  /ui/interfaces/wizard/inc_top.tmpl
do
  if [ -f "$file" ] && ! grep -q "${TP_HOSTNAME}/css/base" "$file"; then
    sed -i "s|</head>|${sheets}</head>|g" "$file"
  fi
done
