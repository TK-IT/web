#!/bin/bash
set -euo pipefail

# TODO wait for database to be ready in a proper way
sleep 20

# We run migration on container startup both in development and production. We
# do this because: 1, we never run more than one instance of the web server on
# the same database, 2, we don't have problems with some minutes of downtime if
# somethings goes wrong, 3, we always deploy by hand and 4, it simple. See
# https://pythonspeed.com/articles/schema-migrations-server-startup/ why you
# shouldn't do this if any of the above does not apply.
./manage.py migrate

./manage.py collectstatic --noinput --clear

exec "$@"
