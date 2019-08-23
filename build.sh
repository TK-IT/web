#!/bin/bash

set -euo pipefail

echo "Building tkweb/apps/barplan/static/barplan.min.js with Docker..."
(
cd tkweb/apps/barplan
TMP="barplan-tmp.js"
TAG=localhost/barplan:latest
docker build --quiet -t "$TAG" .
docker run --rm --entrypoint /bin/sh "$TAG" -c "cat dist/barplan.min.js" > "$TMP"
mv "$TMP" "tkweb/apps/barplan/static/barplan.min.js"
)
