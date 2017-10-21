#!/bin/sh
set -e

if [ "x$DJANGO_MANAGEPY_MIGRATE" = 'xon' ]; then
    python3 manage.py migrate --noinput
fi

if [ "x$DJANGO_MANAGEPY_COLLECTSTATIC" = 'xon' ]; then
    python3 manage.py collectstatic --noinput
fi

exec "$@"
