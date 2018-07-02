#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

cd "$DIR" || exit

pipenv run ./manage.py updateical --settings=tkweb.settings.prod
python run ./manage.py delete_marked_images --settings=tkweb.settings.prod
