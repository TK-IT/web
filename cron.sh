#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

cd "$DIR" || exit

.venv/bin/python ./manage.py updateical --settings=tkweb.settings.prod
.venv/bin/python ./manage.py delete_marked_images --settings=tkweb.settings.prod
