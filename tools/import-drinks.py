import os
import sys
import argparse


def read_input(drink_file):
    drinks = []
    for line in drink_file:
        if line.startwith('='):
            name = line[1:].strip()
            currentdrinkdict = {
                    'name': name,
                    'soda': '',
                    'price': '',
                    'serving': '',
                    'sprut': [],
                    }
            drinks.append(currentdrinkdict)
        elif line.startwith('--'):
            currentsoda = line[2:].strip()
            currentdrinkdict['soda'] = currentsoda
        elif line.startswith("-"):
            sprutdic = {'name': '',
                        'amount': '',
                        'sirup': False}

            currentspirit = line[1:].strip()
            amount = ''
            for s in currentspirit.split():
                if s.isdigit():
                    amount = s
            if amount == '':
                sprutdic['sirup'] = True
                sprutdic['amount'] = '0'
            else:
                sprutdic['amount'] = amount
            
            currentspirit = currentspirit.split('-', 1)[-1]
            sprutdic['name'] = currentspirit

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
    from tkweb.apps.drinks.models import Drinks, Sprut
    for drinkdic in drinks:
        drink = Drinks(name=drinkdic['name'],
                       serving=drinkdic['serving'],
                       soda=drinkdic['soda'])
        drink.save()
        for sprutdic in drinkdic['sprut']:
            sprut = Sprut(name=sprutdic['name'],
                          amount=sprutdic['amount'],
                          drink=drink,
                          sirup=sprutdic['sirup'])
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
        drinks = read_drinks(drinks_file)
        write_to_db(drinks)


if __name__ == "__main__":
    main()
