#!/bin/bash
set -euo pipefail

./manage.py collectstatic --noinput --clear

exec "$@"
