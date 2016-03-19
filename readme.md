# TÅGEKAMMERETS nye webside

## Udviklingsmiljø

Det er en forudsætning at maskinen har en fungerende python (3.3 eller nyere) installation med `pip`.

Brug nedstående til at klone git-repoet, sættet et virtualenv op, installere alle pakker og oprette en database.

```shell
git clone https://github.com/TK-IT/web.git
cd web
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./manage.py migrate --settings=tkweb.settings.dev
./manage.py createsuperuser --settings=tkweb.settings.dev
```

Konfigurationen er delt i flere moduler. `manage.py` bruger enten miljøvariabelen `DJANGO_SETTINGS_MODULE` eller en parameter til at bestemme hvilken konfiguration der skal bruges. For at køre udviklingsserveren med udviklingskonfigurationen skriv:

```shell
./manage.py runserver --settings=tkweb.settings.dev
```

### Udviklingsmiljø for Windows-noobs

Det er en forudsætning, at have en python (3.3 eller nyere) installation med `pip`.

I cmd kan nedenstående give samme opsætning, som ovenstående;

```shell
git clone https://github.com/TK-IT/web.git
cd web
python3 -m venv venv
PATH\TO\ENV\Scripts\activate
pip install -r requirements.txt
python manage.py migrate --settings=tkweb.settings.dev
python manage.py createsuperuser --settings=tkweb.settings.dev
python manage.py runserver --settings=tkweb.settings.dev
```


