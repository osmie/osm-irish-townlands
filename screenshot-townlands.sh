#! /bin/bash

set -o errexit
set -o nounset
cd $(dirname $0)


DATE=$(date -I)
nik2img.py townlands-hypatia.xml /var/www/celtic-knot-creator.com/celticknotcreator/static/townland-overview/townlands-${DATE}.png --bbox -11.030 55.665 -5.098 51.166 -d 4000 4000
