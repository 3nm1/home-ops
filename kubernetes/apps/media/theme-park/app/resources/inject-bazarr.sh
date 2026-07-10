#!/bin/sh
set -eu

: "${TP_HOSTNAME:?TP_HOSTNAME is required}"
: "${TP_THEME:=hotpink}"

base="https://${TP_HOSTNAME}"
sheets="<link rel='stylesheet' href='${base}/css/base/bazarr/bazarr-base.css'>"
sheets="${sheets} <link rel='stylesheet' href='${base}/css/theme-options/${TP_THEME}.css'>"

mkdir -p /ui
cp -a /app/bin/frontend/build/. /ui/

file=/ui/index.html
if [ -f "$file" ] && ! grep -q "${TP_HOSTNAME}/css/base" "$file"; then
  sed -i "s|</head>|${sheets}</head>|g" "$file"
fi
