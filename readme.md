# TÅGEKAMMERETS webside

Websiden er skrevet i Django med Bootstrap 3 som frontend framework.
Den meste funktionalitet kan findes i apps.

- [`tkweb/apps/gallery`](tkweb/apps/gallery) indeholder galleriet inklusiv
  upload fuktionalitet,
- [`tkweb/apps/calendar`](tkweb/apps/calendar) henter et icalendar feed og viser
  det som HTML,
- [`tkweb/apps/jubi`](tkweb/apps/jubi) indeholder jubilæumssiderne som
  [flatpages](https://docs.djangoproject.com/en/1.8/ref/contrib/flatpages/) og
  de tilhørende statiske filer,
- [`tkweb/apps/tkbrand`](tkweb/apps/tkbrand) er en lille HTML kopi af LaTeX
  pakken `tket.sty` til at skrive TÅGEKAMMERET med hoppe-danse-skrift,
- [`tkweb/apps/redirect`](tkweb/apps/redirect) tager sig af vidrestilling af
  URLer fra den gamle PHP-side.
- [`tkweb/apps/idm`](tkweb/apps/idm) er en ikke-offentlig app til at ændre
  persondata og maillister.
- [`tkweb/apps/eval`](tkweb/apps/eval) er en ikke-offentlig wiki til evalueringer.
- [`tkweb/apps/regnskab`](tkweb/apps/regnskab) tager sig af
  krydslisteregnskabet. Den er afhængig af [`tkweb/apps/idm`](tkweb/apps/idm),
  [`tkweb/apps/krydsliste`](tkweb/apps/krydsliste) og
  [`tkweb/apps/uniprint`](tkweb/apps/uniprint).
- [`tkweb/apps/krydsliste`](tkweb/apps/krydsliste) tager sig af opsætning og
  udskrivning af fysiske krydslister.
- [`tkweb/apps/uniprint`](tkweb/apps/uniprint) er en webapplikation til at
  printe på A2 printeren gennem CUPS.
- [`tkweb/apps/drinks`](tkweb/apps/drinks) giver et GUI til SEKR TeX, samt tilføjer muligheden for at gemme drinks og barkort til databasen.
- [`tkweb/apps/barplan`](tkweb/apps/barplan) er en GUI som SEKR kan bruge til at lave en barplan.

Under [`templates`](templates) findes Django HTML-templates som er det der
bliver vist til brugeren.

De 'statiske' sider (Om TK, Arrangementer, BEST/FU osv.) ligger i databasen som
[flatpages](https://docs.djangoproject.com/en/1.8/ref/contrib/flatpages/) og kan
nemt ændres fra admin-interfacet.

[`static-src`](static-src) indeholder statiske filer (grafik, css, js) samt
[Bootstrap 3](http://getbootstrap.com) som et `git submodule`.

[`tkweb/settings`](tkweb/settings) indeholder konfigurationen. Den er delt op i
flere moduler der nedarver fra hinanden. Se også under
[Udviklingsmiljø](#udviklingsmiljø).

## Udviklingsmiljø

Det er en forudsætning at maskinen har en fungerende python installation med
[`pipenv`](https://docs.pipenv.org/), som kan installeres med `pip`.

En mysql installation er også påkrævet så `mysql_client` er tilgængelig, f.eks. skal man installere pakken `libmysqlclient-dev` på Ubuntu/Debian.

Brug nedenstående til at klone git-repoet, sættet et python \[3.3, 3.7) virtualenv op,
installere alle pakker og oprette en database.

```shell
git clone --recursive https://github.com/TK-IT/web.git
cd web
pipenv install --three
pipenv shell
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

## JavaScript i regnskab appen

I [`tkweb/apps/regnskab`](tkweb/apps/regnskab) er der en fil,
[regnskab.es6x](tkweb/apps/regnskab/static/regnskab/regnskab.es6x),
der bruger ECMAScript 6 features og JSX.
Denne oversættes vha. følgende kommando til en JavaScript-fil der kan køre i browseren:

```shell
tools/babel-compile.py tkweb/apps/regnskab/static/regnskab/regnskab.es6x
```

Det kræver at `dukpy` er installeret
(vha. `.venv/bin/pip install dukpy`).

Desuden er der JavaScript tests i
[tkweb/apps/regnskab/tests.js](tkweb/apps/regnskab/tests.js)
som køres af `manage.py test` når `dukpy` er installeret.

## JavaScript i barplan appen

I [`tkweb/apps/barplan`](tkweb/apps/barplan) er der et
TypeScript+React projekt som skal bygges i en Docker container.

For at generere `tkweb/apps/barplan/static/barplan.min.js`,
skal du installére Docker og køre følgende script i roden af tkweb-repositoriet:

```shell
./build.sh
```

## Prodekanus

For informationer om siden på prodekanus
se [readme-prodekanus.md](readme-prodekanus.md).
