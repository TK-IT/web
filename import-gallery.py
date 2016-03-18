import os
import sys
from datetime import datetime
import imghdr

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tkweb.settings.dev")

import django
from django.core.files import File
from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from tkweb.apps.gallery.models import Album, Image

rootdir = sys.argv[1]

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

django.setup()
Album.objects.all().delete()

for yearFolder in os.listdir(rootdir):
    yearStr = yearFolder[3:5]
    if int(yearStr) > 50:
        yearStr = "19" + yearStr
    else:
        yearStr = "20" + yearStr
    print('===', yearStr, "===")

    for eventFolder in os.listdir(os.path.join(rootdir, yearFolder)):
        eventNo = eventFolder[:2]
        eventalbum = True
        if int(eventNo) > 85:
            eventalbum = False

        eventStr = eventFolder[3:]
        eventStr = replace_all(eventStr, replDict)

        print(' ' + eventStr)
        album = Album()
        album.title = eventStr
        album.publish_date = datetime.today() #TODO Find a better date
        album.eventalbum = eventalbum
        album.gfyear = int(yearStr)
        album.slug = slugify(yearStr + "-" + eventStr) #TODO Find a better slug
        album.save()

        for orgiFolder in os.listdir(os.path.join(rootdir, yearFolder,
                                                  eventFolder)):
            filelist = os.listdir(os.path.join(rootdir, yearFolder,
                                                   eventFolder, orgiFolder))
            missing = []
            for imgName in filelist:
                filepath = os.path.join(rootdir, yearFolder, eventFolder,
                                       orgiFolder, imgName)

                if imghdr.what(filepath):
                    op = open(filepath, "rb")
                    djFile = File(op)
                    img = Image()
                    img.associatedObject = album
                    img.image.save('imgName', djFile, save=False)
                    img.full_clean()
                    img.save()
                else:
                    missing.append(filepath)

            print('  ', eventStr, ': Imported', len(album.images.all()))
            if len(missing) > 0:
                print('   ', '\033[93m', 'Missing files:', missing, '\033[0m')


