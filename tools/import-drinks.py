"""
Import script in old python-drinkskort format.

Remember to set DJANGO_SETTINGS_MODULE and PYTHONPATH
and run inside the venv. Example:

DJANGO_SETTINGS_MODULE=tkweb.settings.dev PYTHONPATH=. pipenv run python tools/import-drinks.py drinks.txt
"""

import os
import sys
import argparse


def read_input(drink_file):
    drinks = []
    for line in drink_file:
        if line.startswith('='):
            name = line[1:].strip()
            secret = False
            if name.startswith('?'):
                secret = True
                name = name[1:].strip()
            currentdrinkdict = {
                    'name': name,
                    'soda': [],
                    'price': '',
                    'serving': '',
                    'sprut': [],
                    'secret': secret,
                    }
            drinks.append(currentdrinkdict)
        elif line.startswith('--'):
            currentsoda = line[2:].strip()
            currentdrinkdict['soda'].append(currentsoda)
        elif line.startswith("-"):
            currentspirit = line[1:].strip()
            amount = ""
            for s in currentspirit.split():
                if s.isdigit():
                    amount = s
            name = currentspirit.split("-", 1)[-1]
            sprutdic = {"name": name, "amount": amount}
            currentdrinkdict["sprut"].append(sprutdic)
        elif line.startswith("$"):
            currentprice = line[1:].strip()
            currentdrinkdict["price"] = currentprice
        elif line.startswith("!"):
            currentserved = line[1:].strip()
            currentdrinkdict["serving"] = currentserved
        elif line.startswith("#"):
            pass
        elif line.startswith("\n"):
            pass
    return drinks


def write_to_db(drinks):
    from tkweb.apps.drinks.models import Drink, Sprut, Soda
    for drinkdic in drinks:
        drink = Drink(name=drinkdic['name'],
                        serving=drinkdic['serving'],
                        price=int(drinkdic['price']),
                        secret=drinkdic['secret'])
        print('Saving %s' % drinkdic['name'])
        drink.save()
        for soda in drinkdic['soda']:
            soda = Soda(name=soda,
                        drink=drink)
            soda.save()
        for sprutdic in drinkdic['sprut']:
            if sprutdic["amount"]:
                amount = int(sprutdic["amount"])
            else:
                amount = None
            sprut = Sprut(name=sprutdic["name"], amount=amount, drink=drink)
            sprut.save()


def setup_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE",
                          "tkweb.settings.dev")
    #sys.path.append('/home/tkammer/tkweb/.venv/lib/python3.5/site-packages')
    #sys.path.append('/home/tkammer/tkweb')

    import django
    django.setup()


def main():
    parser = argparse.ArgumentParser(description="Import drinks to the database from .txt file formated as in www.github.com/tk-it/drinkskort")
    parser.add_argument('filepath', help="The path to the input file")    
    args = parser.parse_args()
    setup_django()

    file_path = args.filepath
    print(file_path)
    with open(file_path, mode='r') as drinks_file:
        drinks = read_input(drinks_file)
        write_to_db(drinks)


if __name__ == "__main__":
    main()
