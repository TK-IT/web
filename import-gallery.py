import os
import sys
from datetime import datetime, date, timedelta
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
        unSlugEventStr = replace_all(eventStr, replDict)

        album = Album()
        album.title = unSlugEventStr
        album.publish_date = date.fromtimestamp(0) # Set 1970-01-01 as placeholder timestamp
        album.eventalbum = eventalbum
        album.gfyear = int(yearStr)
        album.slug = slugify(eventStr) # The old title should be a perfect
                                       # slug. We slugify() to be sure.
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

                    #Set album date from last image with non 1970 date.
                    if img.date != datetime.fromtimestamp(0):
                        album.publish_date = img.date
                else:
                    missing.append(filepath)

            print('  ', eventStr, ': Imported', len(album.images.all()))
            if len(missing) > 0:
                print('   ', '\033[93m', 'Missing files:', missing, '\033[0m')


        # If no date has been set. The first album gets the likely GFDATE of
        # the year. Subsequent albums are on the following days
        if album.publish_date != datetime.fromtimestamp(0):
            album.publish_date = date(int(yearStr), 9, 20) + timedelta(days=int(eventFolder[:2]))
        album.save()


