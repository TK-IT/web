# TÅGEKAMMERETS webside

Websiden er skrevet i Django 1.8 LTS med Bootstrap 3 som frontend framework.
Den meste funktionalitet kan findes i apps.
- [`tkweb/apps/gallery`](tkweb/apps/gallery) indeholder galleriet inklusiv
  upload fuktionalitet,
-  [`tkweb/apps/calendar`](tkweb/apps/calendar) henter et icalendar feed og viser
  det som HTML,
- [`tkweb/apps/jubi`](tkweb/apps/jubi) indeholder jubilæumssiderne som
  [flatpages](https://docs.djangoproject.com/en/1.8/ref/contrib/flatpages/) og
  de tilhørende statiske filer,
- [`tkweb/apps/tkbrad`](tkweb/apps/tkbrand) er en lille HTML kopi af LaTeX
  pakken `tket.sty` til at skrive TÅGEKAMMERET med hoppe-danse-skrift,
- [`tkweb/apps/redirect`](tkweb/apps/redirect) tager sig af vidrestilling af
  URLer fra den gamle PHP-side.

Under [`templates`](templates) findes Django HTML-templates som er det der
bliver vist til brugeren.

De 'statiske' sider (Om TK, Arrangementer, BEST/FU osv.) ligger i databasen som
[flatpages](https://docs.djangoproject.com/en/1.8/ref/contrib/flatpages/) og kan
nemt ændres fra admin-interfacet.

[`static-src`](static-src) indeholder statiske filer (grafik, css, js) samt
[Bootstrap 3](http://getbootstrap.com) som et `git submodule`.

[`tkweb/settings`](tkweb/settings) indeholder konfigurationen. Den er delt op i
flere moduler der nedarver fra hindanden. Se også under
[Udviklingsmiljø](#udviklingsmiljø).


## Udviklingsmiljø

Det er en forudsætning at maskinen har en fungerende python installation med
`pip`.

Brug nedstående til at klone git-repoet, sættet et python ≥ 3.3 virtualenv op,
installere alle pakker og oprette en database.

```shell
git clone --recursive https://github.com/TK-IT/web.git
cd web
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./manage.py migrate --settings=tkweb.settings.dev
./manage.py createsuperuser --settings=tkweb.settings.dev
```

Konfigurationen er delt i flere moduler. `manage.py` bruger enten
miljøvariabelen `DJANGO_SETTINGS_MODULE` eller en parameter til at bestemme
hvilken konfiguration der skal bruges. Man skal explicit sætte en af disse. For
at køre udviklingsserveren med udviklingskonfigurationen skriv:

```shell
./manage.py runserver --settings=tkweb.settings.dev
```

#### Windows

I `cmd.exe` på Windows kan man aktivere virtualenv ved at køre
`venv\Scripts\activate` istedet for `source venv/bin/activate`.

## Python 2+3

Koden er Python 3 med Python 2 kompatibilitet. Det vil for det meste sige at du
skal

- bruge `from __future__ import unicode_literals` i moduler,
- dekorere dine klasser med `@python_2_unicode_compatible` og bruge
`__str__()`.

Se
[Django dokumentationen](https://docs.djangoproject.com/en/1.8/topics/python3/)
og issue #31 for motivationen.

## LESS og CSS

For ikke at have node.js som dependency på serveren er det nødvendigt at have en
compilet CSS version af alle LESS filerne i git. Det er indeholdt i
[`static-src/style.min.css`](static-src/style.min.css) og
[`static-src/style.min.css.map`](static-src/style.min.css.map).

For at compile dette kræver det LESS og node.js. Med en fungerende node.js
installation kan LESS og en CSS-minifier installeres med
```shell
npm install -g less less-plugin-clean-css
```
For at genere nye CSS filer køres
```shell
cd static-src
lessc --clean-css --source-map style.less style.min.css
```
