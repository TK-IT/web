# -*- coding: utf-8 -*-
'''
Generate barcard.tex and mixing.tex from given drinks list.
Running this script directly is usually not necessary; run make instead.
Usage is described in BRUGSANVISNING.txt (in Danish).

Authors:
    Mads Fabricius Schmidt
    Jakob Rørsted Mosumgaard
    Mathias Rav
'''

from __future__ import unicode_literals

import codecs
import argparse


# Encoding is always utf8!
ENCODING = 'utf8'

columns_modes = {
    'old': [
        ('Navn', 'name'),
        ('Sprut', 'ingredients'),
        ('Sodavand', 'soda'),
        ('Servering', 'served'),
        ('Pris', 'price'),
    ],
    'new': [
        ('Navn', 'name'),
        ('Pris', 'price'),
        ('Servering', 'served'),
        ('Sprut', 'ingredients'),
        ('Sodavand', 'soda'),
    ],
}


def readdrinks(drinksfile, verbose):
    drinks = []

    # Read the file line by line
    for line in drinksfile:
        # Get the current drink
        if line.startswith('='):
            name = line[1:].strip()
            alternative = ''

            # Sort into secret and normal drinks
            if name.startswith('?'):
                secret = True
                name = name[1:].strip()
            else:
                secret = False

            if '=' in name:
                # Drink has alternative name
                names = name.split('=')
                name = names[0].strip()
                alternative = names[1].strip()

            currentdrinkdict = {
                'name': name,
                'alternative': alternative,
                'soda': [],
                'spirit': [],
                'served': '',
                'servedbarcard': '',
                'price': '',
                'secret': secret,
            }
            drinks.append(currentdrinkdict)

        # Soda
        elif line.startswith('--'):
            currentsoda = line[2:].strip()
            currentdrinkdict['soda'].append(currentsoda)

        # Spirit
        elif line.startswith('-'):
            currentspirit = line[1:].strip()
            currentdrinkdict['spirit'].append(currentspirit)

        # served
        elif line.startswith('!'):
            currentserved = line[1:].strip()
            currentdrinkdict['servedbarcard'] = currentserved
            if '!' in currentserved:
                ser = currentserved.split('!')
                currentserved = ser[0].strip()
                barcardserved = ser[1].strip()
                currentdrinkdict['servedbarcard'] = barcardserved
            currentdrinkdict['served'] = currentserved

        # Price
        elif line.startswith('$'):
            currentprice = line[1:].strip()
            currentdrinkdict['price'] = currentprice

        # Comment
        elif line.startswith('#'):
            pass
        # Empty line
        elif line.startswith('\n'):
            pass
        # Unrecognized line.
        else:
            if verbose:
                print('Unrecognized line: ' + line.strip())
            else:
                pass

    return drinks


def generatebarcard(drinks):
    for currentingredients in drinks:
        if currentingredients['secret']:
            # Skip secret drinks
            continue

        drink = currentingredients['name']
        yield r'\drik %s' % drink
        yield r'\til %s' % currentingredients['price']

        # Write every other thing:
        yield r'\med %'

        for spirit in currentingredients['spirit']:
            amount = '\t\t'
            if '-' in spirit:
                # Split returns an array of strings.
                # amount is the first of these
                amount, spirit = spirit.split('-')
                amount = amount.strip() + '\t'
                spirit = spirit.strip()
            yield r'%s& %s \og' % (amount, spirit)

        for soda in currentingredients['soda']:
            yield '\t\t& %s \og' % soda

        # for served in currentingredients['served']:
        served = currentingredients['served']
        if served.lower() == u'drinksglas':
            yield '\t\t' + r'\serveret I et %s med is' % served.lower()
        elif served.lower() == u'fadølsglas':
            yield '\t\t' + r'\serveret I et %s med is' % served.lower()
        else:
            yield '\t\t' + r'\serveret %s' % served
        yield ''


def generatemixingcard(drinks, columns, use_alternatives):
    """
    `columns` is a list of (name, key)-tuples where key is one of
    (name, ingredients, soda, served, price),
    and name is the descriptive name to put in column headers.
    """
    # Do TeX-stuff
    yield r'\begin{tabular}{lllll}'

    yield r'\toprule %s \\' % ' & '.join('\\bfseries ' + name for
                                         name, key in columns)
    yield r'\midrule'

    # Loop over all drinks
    for drinknumber, currentingredients in enumerate(drinks):
        name = currentingredients['name']
        alternative = currentingredients['alternative']
        if alternative and use_alternatives:
            name = '%s (%s)' % (name, alternative)

        if drinknumber % 2 == 0:
            yield '\\rowcolor{Gray}%'

        NEWLINE = r'\\'

        ingredients = ', '.join(' '.join(part for part in spirit.split('-'))
                                for spirit in currentingredients['spirit'])

        soda = ', '.join(currentingredients.get('soda', []))

        served = currentingredients['servedbarcard'].capitalize()

        price = currentingredients['price'] + ' kr'

        fields = dict(
            name=name,
            ingredients=ingredients,
            soda=soda,
            served=served,
            price=price,
        )

        cells = ' & '.join(fields[key] for name, key in columns)

        mixingcardline = cells + NEWLINE

        yield mixingcardline

    yield r'\bottomrule'
    yield r'\end{tabular}'


#####################################
# The function which does the magic #
#####################################
def makedrinks(filename, verbose, sortbarcards, alternative, columns):
    with codecs.open(filename, 'r', encoding=ENCODING) as drinksfile:
        drinks = readdrinks(drinksfile, verbose)

    # Sort the drinks on the barcard by price
    if sortbarcards:
        price_sorted_drinks = sorted(drinks, key=lambda drink: drink['price'])
        drinks = price_sorted_drinks

    with codecs.open('barcard.tex', 'w', encoding=ENCODING) as barcard:
        for line in generatebarcard(drinks):
            barcard.write('%s\n' % line)

    # Sort the drinks on the micing card by name
    drinks_sorted = sorted(drinks, key=lambda drink: drink['name'])

    columns = columns_modes[columns]

    # Open file for the mixing card ("blandeliste")
    with codecs.open('mixing.tex', 'w', encoding=ENCODING) as mixingcard:
        for line in generatemixingcard(drinks_sorted, columns, alternative):
            mixingcard.write('%s\n' % line)


######################################
# Parsing of arguments to the script #
######################################
def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('filename',
                        help='Text file containing drinks to display')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Print unrecognized lines')
    parser.add_argument('-s', '--sortbarcards',
                        action='store_true',
                        help='Sort drinks by price')
    parser.add_argument('-a', '--alternative',
                        action='store_true',
                        help='Display alternative names in parentheses')
    parser.add_argument('-c', '--columns',
                        choices=sorted(columns_modes.keys()), default='new',
                        help='Order of columns in mixing card')

    args = parser.parse_args()
    makedrinks(**vars(args))


# Run the function if file is called directly
if __name__ == '__main__':
    main()
