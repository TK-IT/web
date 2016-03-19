# TÅGEKAMMERETS nye webside

## Python 2+3

Koden er Python 3 med Python 2 kompatibilitet. Det vil for det meste sige at du
skal

  * bruge `from __future__ import unicode_literals` i moduler,
  * dekorere dine klasser med `@python_2_unicode_compatible` og bruge
`__str__()`.

Se
[Django dokumentationen](https://docs.djangoproject.com/en/1.8/topics/python3/)
og issue #31 for motivationen.

## Udviklingsmiljø

Det er en forudsætning at maskinen har en fungerende python installation med
`pip`.

Brug nedstående til at klone git-repoet, sættet et python ≥ 3.3 virtualenv op,
installere alle pakker og oprette en database.

```shell
git clone https://github.com/TK-IT/web.git
cd web
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./manage.py migrate --settings=tkweb.settings.dev
./manage.py createsuperuser --settings=tkweb.settings.dev
```

Konfigurationen er delt i flere moduler. `manage.py` bruger enten
miljøvariabelen `DJANGO_SETTINGS_MODULE` eller en parameter til at bestemme
hvilken konfiguration der skal bruges. For at køre udviklingsserveren med
udviklingskonfigurationen skriv:

```shell
./manage.py runserver --settings=tkweb.settings.dev
```

### Udviklingsmiljø for Windows-noobs

I `cmd.exe` kan nedenstående give samme opsætning, som ovenstående;

```shell
git clone https://github.com/TK-IT/web.git
cd web
python3 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate --settings=tkweb.settings.dev
python manage.py createsuperuser --settings=tkweb.settings.dev
python manage.py runserver --settings=tkweb.settings.dev
```
