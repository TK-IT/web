import json
import argparse

from legacy.base import Regnskab, read_regnskab, Person


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()

    with open(args.filename, 'rb') as fp:
        regnskab = read_regnskab(fp)
    persons = [
        dict(id=i, sort_key=i, name=p.navn,
             titles=('%s %s' % (p.titel, p.aliaser)).split())
        for i, p in enumerate(sorted(regnskab.personer, key=lambda p: p.skjul))]
    print(json.dumps(persons, indent=4))


if __name__ == "__main__":
    main()
