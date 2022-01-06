#! /bin/bash

set -o errexit

cd $(dirname $0)
ROOT=$(pwd)

CURR_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ $CURR_BRANCH != 'master' ]] ; then
    echo "[django-osm-irish-townlands] Not on master git branch. Exiting"
    exit 1
fi

if ! git diff --exit-code >/dev/null ; then
    echo "[django-osm-irish-townlands] Uncommited changes. Exiting"
    git diff --exit-code
    exit 2
fi

VERSION=$(date '+%Y%m%d%H%M%S')
clog -F --setversion=${VERSION} -C CHANGELOG.md || true

git tag ${VERSION}
