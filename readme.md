# TÅGEKAMMERETS nye webside

## Udviklingsmiljø

Det er en forudsætning at maskinen har en fungerende python installation med `pip` og `virtualenv`.

Brug nedstående til at klone git-repoet, sættet et virtualenv op, installere alle pakker og oprette en database.

```shell
git clone https://github.com/TK-IT/web.git
cd web
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
./manage.py migrate --settings=tkweb.settings.dev
./manage.py createsuperuser --settings=tkweb.settings.dev
```

Konfigurationen er delt i flere moduler. `manage.py` bruger enten miljøvariabelen `DJANGO_SETTINGS_MODULE` eller en parameter til at bestemme hvilken konfiguration der skal bruges. For at kører udviklingsserveren med udviklingskonfigurationen skriv:

```shell
./manage.py runserver --settings=tkweb.settings.dev
```
