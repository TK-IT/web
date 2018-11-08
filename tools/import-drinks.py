import os
import sys
import argparse

def setup_django():
    os.enviro.setdefault("DJANGO_SETTINGS_MODULE",
                         "tkweb.settings.prod")
    sys.path.append('/home/tkammer/tkweb/.venv/lib/python3.5/site-packages')
    sys.path.append('/home/tkammer/tkweb')

    import django
    django.setup()

def main():
    parser = argparse.ArgumentParser(description="Import drinks to the database from .txt file formated as in www.github.com/tk-it/drinkskort")
    parser.add_argument('filepath', help="The path to the input file")    
    args = parser.parse_args()

    file_path = args.filepath
    print(file_path)

if __name__ == "__main__":
    main()
