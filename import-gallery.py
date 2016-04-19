# You can use `find . -name '*.DS_Store' -type f -delete` if you operating
# system is a bitch and pollutes you folders

import os
from os.path import join
import sys
import re
from datetime import datetime, date, timedelta
import imghdr
import argparse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tkweb.settings.dev")

import django
from django.core.files import File
from django.utils.text import slugify
django.setup()
from tkweb.apps.gallery.models import Album, Image

parser = argparse.ArgumentParser(description="Delete all old Albums and Images. Transverses the rootdir and makes new Albums. With arguments it will also add Images.")
parser.add_argument('-c', "--check", action="store_true",
                    help="Add the image to the imagemodel. Does not save it. This checks if the model can handle the filetype")
parser.add_argument('-s', "--save", action="store_true",
                    help="Save the images in the database and generate thumbnails. Implies -c")
parser.add_argument('rootdir', help="The path to the 'Billeder' folder from the old webpage")

args = parser.parse_args()

rootdir = args.rootdir
skipped = []
missingFromResizedGlobal = []

replDict = {"_": " ",
       "ae": "æ",
       "AE": "Æ",
       "oe": "ø",
       "OE": "Ø",
       "aa": "å",
       "AA": "Å",}

def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text

def printi(n, t1, t2=""):
    indent = ""
    for i in range(n):
        indent += "  "
    print(indent, t1, t2)

Album.objects.all().delete()

for yearFolder in os.listdir(rootdir):
    p = re.compile("^[0-9]{2}-[0-9]{4}$")
    if not p.match(yearFolder):
        skipped.append(os.path.join(rootdir, yearFolder))
        continue

    yearStr = yearFolder[3:5]
    if int(yearStr) > 50:
        yearStr = "19" + yearStr
    else:
        yearStr = "20" + yearStr
    #printi(0, yearStr)

    for eventFolder in os.listdir(os.path.join(rootdir, yearFolder)):
        p = re.compile("^[0-9]{2}-[\w\-]")
        if not p.match(eventFolder):
            skipped.append(os.path.join(rootdir, yearFolder, eventFolder))
            continue

        eventNo = eventFolder[:2]
        eventalbum = True
        if int(eventNo) > 85:
            eventalbum = False

        if int(yearStr) == 2011 and eventFolder == '32-Brianfodring':
            eventStr = "Brianfodring 2"
        elif int(yearStr) == 2011 and eventFolder == '51-Brianfodring':
            eventStr = "Brianfodring 3"
        else:
            eventStr = eventFolder[3:]

        unSlugEventStr = replace_all(eventStr, replDict)

        album = Album()
        album.title = unSlugEventStr
        album.publish_date = None
        album.eventalbum = eventalbum
        album.gfyear = int(yearStr)
        album.slug = slugify(eventStr) # The old title should be a perfect
                                       # slug. We slugify() to be sure.
        album.oldFolder = os.path.join(yearFolder, eventFolder)
        album.save()

        orgiFilelist = []
        resizedFilelist = []

        for orgiOrFile in os.listdir(os.path.join(rootdir, yearFolder,
                                                  eventFolder)):
            if orgiOrFile in ("thumbs"):
                # We have a 'thumbs' folder, ignore
                continue

            elif orgiOrFile in ("Originale", 'originale', 'Oiginale',
                                'original', 'Originale-crop'):

                # We have a 'original' folder
                l = os.listdir(os.path.join(rootdir, yearFolder, eventFolder,
                                            orgiOrFile))
                orgiFilelist.extend([join(orgiOrFile, f) for f in l])

            elif os.path.basename(os.path.join(rootdir, yearFolder,
                                               eventFolder, orgiOrFile)):
                # We have a file
                resizedFilelist.append(orgiOrFile)

            else:
                # We have a strange folder
                skipped.append(os.path.join(rootdir, yearFolder,
                                            eventFolder, orgiOrFile))
        orgiFilelist.sort()
        resizedFilelist.sort()

        if not orgiFilelist and not resizedFilelist:
            # We have a empty album. Don't look further
            continue

        strippedOrgiFileList = [os.path.basename(f) for f in orgiFilelist]

        def diff(a, b):
            b = set(b)
            return [aa for aa in a if aa.lower() not in (bb.lower() for bb in b)]

        missingFromResized = []
        missingFromOriginale= []

        d = diff(resizedFilelist, strippedOrgiFileList)
        for i in d:
            missingFromOriginale.append(i)

        d = diff(strippedOrgiFileList, resizedFilelist)
        for i in d:
            missingFromResized.append(i)


        filelist = []

        if not missingFromOriginale:
            # There is nothing missing from orginale
            for f in orgiFilelist:
                fullpath = os.path.join(rootdir, yearFolder, eventFolder, f)
                if os.path.isfile(fullpath):
                    filelist.append(fullpath)
                else:
                    skipped.append(fullpath)

            if missingFromResized:
                missingFromResizedGlobal.extend([os.path.join(rootdir, yearFolder, eventFolder,
                                                    f) for f in missingFromResized])

        elif not orgiFilelist:
            # There is no 'orginal' folder, use 'resized' folder
            for f in resizedFilelist:
                fullpath = os.path.join(rootdir, yearFolder, eventFolder, f)
                if os.path.isfile(fullpath):
                    filelist.append(fullpath)
                else:
                    skipped.append(fullpath)

        #printi(3, filelist)

        if not filelist:
            print("===", os.path.join(rootdir, yearFolder, eventFolder), "===")
            printi(2, "orgiFilelist", orgiFilelist)
            printi(2, "resizedFilelist", resizedFilelist)
            printi(2, "missingFromOriginale", missingFromOriginale)
            printi(2, "missingFromResized", missingFromResized)
            print("")

        else:
            if args.check or args.save:
                for filepath in filelist:
                    if imghdr.what(filepath):
                        op = open(filepath, "rb")
                        djFile = File(op)
                        img = Image()
                        img.album = album
                        img.image = djFile

                        if os.path.basename(filepath) in missingFromResized:
                            img.notPublic = True

                        img.full_clean()
                        if args.save:
                            img.save() # This prints a newline

                        #Set album date from last image with a date.
                        if not img.date == None:
                            album.publish_date = img.date
                    else:
                        skipped.append(filepath)

        album.save()

print('Missing from resized / Not public images:')
for l in missingFromResizedGlobal:
    printi(2, l)

print('Skipped files:')
for l in skipped:
    printi(2, l)
