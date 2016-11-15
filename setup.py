# License:
#   "THE BEER-WARE LICENSE" (Revision 42):
# <TKIT@TAAGEKAMMERET.dk> wrote these files. As long as you retain this notice
# you can do whatever you want with this stuff. If we meet some day, and you
# think this stuff is worth it, you can buy us some beer in return. TÅGEKAMMERET

import os
from setuptools import find_packages, setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.dirname(os.path.abspath(__file__))))

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

setup(
    name='regnskab',
    version='0.1',
    packages=find_packages(include=['regnskab', 'regnskab.*']),
    include_package_data=True,
    license='THE BEER-WARE LICENSE',
    description='App for use by INKA in TÅGEKAMMERET',
    long_description=README,
    url='https://www.TAAGEKAMMERET.dk/',
    author='Mathias Rav',
    author_email='FORM13@TAAGEKAMMERET.dk',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Intended Audience :: Developers',
        # 'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
