# encoding: utf8
from __future__ import unicode_literals

# You can use `find . -name '*.DS_Store' -type f -delete` if you operating
# system is a bitch and pollutes you folders


### Fremgangmåde til endeligt import. ###
# 1. På en frossen udgave af Billede mappen køres `import-gallery.py -c`. Det
# tager et par minutter.
#
# 2. På alle fejl der rapportes, tages der stilling til hvad der skal gøres.
# Eks. .m4v filer laves til .mp4, mærkelige filer eller mapper slettes eller
# billeder kopieres fra resized til orginale.
#
# 3. Når `import-gallery.py -c` kun rapportere fejl der ikke skal gøres noget
# ved, kan man slå `generateImageThumbnails` fra i tkweb/apps/gallery/models.py
# ved at udkommentere `@receiver(…)`. Derefter køres `import-gallery.py -s` for
# importere alle filerne til filsystement og databasen, men uden at genrere
# thumbnails.
#
# 4. Hvis det ikke giver anledning til fejl kan man slå
# `generateImageThumbnails` til igen og køre en endelig import med
# `import-gallery.py -s`. Det kommer sansynlig vis til at tage timer.
#
# 5. Gå på druk imens man venter.


import os
from os.path import join
import re
import argparse
import subprocess

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tkweb.settings.prod")

import django
from django.core.files import File
from django.core.exceptions import ValidationError
from django.utils.text import slugify
django.setup()
from tkweb.apps.gallery.models import Album, BaseMedia, Image, GenericFile

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

# The slug for the files in the Albums in this list will be forced to be from
# the name instead of EXIF
slugOverwrite = ['11-0708/92-Loebesedler']
slugOverwrite = [os.path.join(rootdir, p) for p in slugOverwrite]

# Files in this list will be compaired with the resized folder, but not
# imported afterwards. This break links from the old URLs
deleteFiles = ['18-1415/90-AArets_gang/Originale/20140925-142750a.jpg',
               '18-1415/90-AArets_gang/Originale/20140926-040012a.jpg',
               '18-1415/49-Sidste_torsdagsmoede/Originale/20150917-182218a.jpg',
               '18-1415/20-Luciadag/Originale/20141212-130401a.jpg',
]
deleteFiles = [os.path.join(rootdir, p) for p in deleteFiles]

notPublicFiles = ['13-0910/09-J-Dag/IMG_4874.JPG',
'13-0910/09-J-Dag/IMG_4879.JPG',
'13-0910/31-Foraarsfest/IMG_0807.JPG',
'13-0910/36-Majfest_med_revy/Maj fest 023.jpg',
'13-0910/36-Majfest_med_revy/Maj fest 025.jpg',
'13-0910/36-Majfest_med_revy/Maj fest 142.jpg',
'13-0910/36-Majfest_med_revy/Maj fest 143.jpg',
'13-0910/49-TK-Open/IMG_2461.JPG',
'13-0910/49-TK-Open/IMG_2487.JPG',
'13-0910/53-Sidste_moede/IMG_2916.JPG',
'13-0910/53-Sidste_moede/IMG_2941.JPG',
'13-0910/53-Sidste_moede/IMG_3058.JPG',
'14-1011/05-Foerste_Reception/IMG_0043.JPG',
'14-1011/16-J-dag/IMG_0990.JPG',
'14-1011/24-Foredrag_med_Rune_T_Kidde/DSCF4239.JPG',
'14-1011/33-LPT_plus_En_kasse_i_KASS/IMG_0006.JPG',
'14-1011/33-LPT_plus_En_kasse_i_KASS/IMG_0021.JPG',
'14-1011/38-Anden_Reception/IMG_0313.JPG',
'14-1011/38-Anden_Reception/IMG_0327.JPG',
'14-1011/38-Anden_Reception/IMG_0356.JPG',
'14-1011/42-Karnevalsfest/IMG_0688.JPG',
'14-1011/42-Karnevalsfest/IMG_0689.JPG',
'14-1011/42-Karnevalsfest/IMG_0690.JPG',
'14-1011/50-AEggepustning/IMG_1422.JPG',
'14-1011/56-Majrevy/Majrevy (082).JPG',
'14-1011/56-Majrevy/Majrevy (122).JPG',
'14-1011/56-Majrevy/Majrevy (123).JPG',
'14-1011/56-Majrevy/Majrevy (158).JPG',
'14-1011/56-Majrevy/Majrevy (211).JPG',
'14-1011/56-Majrevy/Majrevy (292).JPG',
'14-1011/56-Majrevy/Majrevy (293).JPG',
'14-1011/56-Majrevy/Majrevy (294).JPG',
'14-1011/56-Majrevy/Majrevy (296).JPG',
'14-1011/56-Majrevy/Majrevy (297).JPG',
'14-1011/56-Majrevy/Majrevy (298).JPG',
'14-1011/65-TK-Grill/IMG_3254.JPG',
'14-1011/65-TK-Grill/IMG_3258.JPG',
'15-1112/03-Diverse_forloev/20110702-124824.jpg',
'15-1112/03-Diverse_forloev/20110702-124827.jpg',
'15-1112/03-Diverse_forloev/20110702-163007.jpg',
'15-1112/03-Diverse_forloev/20110904-133848.jpg',
'15-1112/03-Diverse_forloev/20110904-135746.jpg',
'15-1112/03-Diverse_forloev/20110904-163447.jpg',
'15-1112/03-Diverse_forloev/20110904-163457.jpg',
'15-1112/03-Diverse_forloev/20110904-170124.jpg',
'15-1112/03-Diverse_forloev/20110904-170141.jpg',
'15-1112/06-Foerste_reception/IMG_4997.JPG',
'15-1112/06-Foerste_reception/IMG_5003.JPG',
'15-1112/07-HSTR/20111001-114555.jpg',
'15-1112/08-Stiftelsesfest/20111007-204407.jpg',
'15-1112/12-J-dag/IMG_5518.JPG',
'15-1112/12-J-dag/IMG_5562.JPG',
'15-1112/12-J-dag/IMG_5684.JPG',
'15-1112/13-BODYCRASHING/20111116-185358.jpg',
'15-1112/13-BODYCRASHING/20111116-185450.jpg',
'15-1112/16-Hennebergs_reception/IMG_5949.JPG',
'15-1112/16-Hennebergs_reception/IMG_5983.JPG',
'15-1112/17-Foerst_til_en_kasse_mod_Alkymia/IMG_6012.JPG',
'15-1112/17-Foerst_til_en_kasse_mod_Alkymia/IMG_6019.JPG',
'15-1112/23-Julerevy/IMG_7740.JPG',
'15-1112/23-Julerevy/IMG_7956.JPG',
'15-1112/23-Julerevy/IMG_7970.JPG',
'15-1112/23-Julerevy/IMG_7994.JPG',
'15-1112/23-Julerevy/IMG_7996.JPG',
'15-1112/23-Julerevy/IMG_7997.JPG',
'15-1112/23-Julerevy/IMG_8000.JPG',
'15-1112/23-Julerevy/IMG_8079.JPG',
'15-1112/23-Julerevy/IMG_8081.JPG',
'15-1112/23-Julerevy/IMG_8147.JPG',
'15-1112/23-Julerevy/IMG_8153.JPG',
'15-1112/23-Julerevy/IMG_8182.JPG',
'15-1112/23-Julerevy/IMG_8183.JPG',
'15-1112/23-Julerevy/IMG_8185.JPG',
'15-1112/23-Julerevy/IMG_8186.JPG',
'15-1112/23-Julerevy/IMG_8189.JPG',
'15-1112/23-Julerevy/IMG_8190.JPG',
'15-1112/23-Julerevy/IMG_8195.JPG',
'15-1112/23-Julerevy/IMG_8197.JPG',
'15-1112/23-Julerevy/IMG_8198.JPG',
'15-1112/23-Julerevy/IMG_8199.JPG',
'15-1112/23-Julerevy/IMG_8202.JPG',
'15-1112/23-Julerevy/IMG_8204.JPG',
'15-1112/23-Julerevy/IMG_8210.JPG',
'15-1112/25-Rengoering_1/IMG_6737.JPG',
'15-1112/25-Rengoering_1/IMG_6745.JPG',
'15-1112/28-Udklaedninger_til_Karneval/20110217-205920.jpg',
'15-1112/28-Udklaedninger_til_Karneval/20120217-210030.jpg',
'15-1112/28-Udklaedninger_til_Karneval/20120217-210224.jpg',
'15-1112/33-Stand-Up/20110311-015735.jpg',
'15-1112/34-OEl-tequila-bowling/DSC_0026.JPG',
'15-1112/36-Rengoering_2/IMG_1092.JPG',
'15-1112/37-Anden_reception/IMG_1157.JPG',
'15-1112/39-En_kasse_i_KASS/IMG_1278.JPG',
'15-1112/40-Dommertraening_ved_unisoen/20120415-141839.jpg',
'15-1112/40-Dommertraening_ved_unisoen/20120415-142248.jpg',
'15-1112/41-Foraarsfest/20120420-202259.jpg',
'15-1112/44-Botanisk_Have/20120510-183709.jpg',
'15-1112/44-Botanisk_Have/20120510-190000.jpg',
'15-1112/46-Kapsejladsen/20120503-141434.jpg',
'15-1112/46-Kapsejladsen/20120503-141440.jpg',
'15-1112/47-Majfest/20120525-232659.jpg',
'15-1112/47-Majfest/20120526-012353.jpg',
'15-1112/52-TK-Grill/20120811-160436.jpg',
'15-1112/52-TK-Grill/20120811-183832.jpg',
'15-1112/53-Haengermorgenmad_og_dekanvelkomst/20120822-104238.jpg',
'15-1112/57-Rushyg/20120901-015604.jpg',
'15-1112/62-NF_hylder_FORM/20120913-194617.jpg',
'15-1112/64-TK-Open/20120919-160621.jpg',
'15-1112/64-TK-Open/20120919-160646.jpg',
'15-1112/65-Sidste_torsdagsmoede/20120920-171434.jpg',
'15-1112/65-Sidste_torsdagsmoede/20120920-175451.jpg',
'15-1112/65-Sidste_torsdagsmoede/20120920-194955.jpg',
'15-1112/65-Sidste_torsdagsmoede/20120920-200808.jpg',
'15-1112/65-Sidste_torsdagsmoede/20120920-202420.jpg',
'15-1112/65-Sidste_torsdagsmoede/20120920-211341.jpg',
'15-1112/65-Sidste_torsdagsmoede/20120920-211352.jpg',
'15-1112/65-Sidste_torsdagsmoede/20120920-213453.jpg',
'15-1112/65-Sidste_torsdagsmoede/20120920-223428.jpg',
'15-1112/90-AArets_gang/20111010-195108.jpg',
'15-1112/90-AArets_gang/20111010-195121.jpg',
'15-1112/90-AArets_gang/20111010-195127.jpg',
'15-1112/90-AArets_gang/20111010-195140.jpg',
'16-1213/10-GF/20120923-183919.jpg',
'16-1213/10-GF/20120923-204328.jpg',
'16-1213/10-GF/20120923-214606.jpg',
'16-1213/36-Foraarsfest/20130413-022304.jpg',]

notPublicFiles = [os.path.join(rootdir, p) for p in notPublicFiles]

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

        # The folders here will be renamed.
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
            b_lower = set(x.lower() for x in b)
            return [x for x in a if x.lower() not in b_lower]

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
            print("=== %s ===" % (os.path.join(rootdir, yearFolder, eventFolder)))
            print("orgiFilelist %s\n\n" % (orgiFilelist))
            print("resizedFilelist %s\n\n" % (resizedFilelist))
            print("missingFromOriginale %s\n\n" % (missingFromOriginale))
            print("missingFromResized %s\n\n" % (missingFromResized))

        else:
            if args.check or args.save:
                i = 0
                for filepath in filelist:
                    if filepath in deleteFiles:
                        continue

                    if os.path.splitext(os.path.basename(filepath))[0][0] == ".":
                        continue

                    op = open(filepath, "rb")
                    file = File(op)
                    ext = os.path.splitext(filepath)[1].lower()
                    if ext in (".png", ".gif", ".jpg", ".jpeg" ):
                        instance = Image(file=file, album=album)
                    elif ext in (".mp3"):
                        instance = GenericFile(file=file, album=album)
                        instance.type = BaseMedia.AUDIO
                    elif ext in (".mp4", ".m4v"):
                        tmpfilename = os.path.splitext(os.path.basename(filepath))[0] + '.mp4'
                        tmpfilepath = os.path.join('/tmp', tmpfilename)
                        ffargs = ['./ffmpeg-3.1.1-64bit-static/ffmpeg', '-y', '-i', filepath] + '-c copy -movflags +faststart'.split() + [tmpfilepath]
                        subprocess.check_call(ffargs)
                        op2 = open(tmpfilepath, "rb")
                        file2 = File(op2)
                        instance = GenericFile(originalFile=file, file=file2, album=album)
                        instance.type = BaseMedia.VIDEO
                    elif ext in (".avi", ".mov"):
                        tmpfilename = os.path.splitext(os.path.basename(filepath))[0] + '.mp4'
                        tmpfilepath = os.path.join('/tmp', tmpfilename)
                        ffargs = ['./ffmpeg-3.1.1-64bit-static/ffmpeg', '-y', '-i', filepath] + '-c:v libx264 -pix_fmt yuv420p -profile:v baseline -level 3.0 -movflags +faststart'.split() + [tmpfilepath]
                        subprocess.check_call(ffargs)
                        op2 = open(tmpfilepath, "rb")
                        file2 = File(op2)
                        instance = GenericFile(originalFile=file, file=file2, album=album)
                        instance.type = BaseMedia.VIDEO
                    elif ext in (".pdf", ".txt"):
                        instance = GenericFile(file=file, album=album)
                        instance.type = BaseMedia.OTHER
                    else:
                        skipped.append(filepath)
                        continue

                    if os.path.basename(filepath) in missingFromResized:
                        instance.notPublic = True

                    if os.path.basename(filepath) in notPublicFiles:
                        instance.notPublic = True

                    instance.forcedOrder = i
                    i += 1
                    try:
                        instance.full_clean()
                    except ValidationError as e:
                        print("=== %s ===" % (os.path.join(rootdir, yearFolder, eventFolder)))
                        print("file", file)
                        print("ValidationError", e)
                        print("")
                        continue

                    # overwrite some slugs
                    p = os.path.join(rootdir, yearFolder, eventFolder)
                    if p in slugOverwrite:
                        instance.slug = slugify(os.path.splitext(os.path.basename(file.name))[0])

                    if args.save:
                        instance.save() # This prints a newline

                    #Set album date from last image with a date.
                    if not instance.date == None:
                        album.publish_date = instance.date
        album.save()

print('Missing from resized / Not public images:')
for l in missingFromResizedGlobal:
    print("%s" % (l))

print('\n\nSkipped files:')
for l in skipped:
    print("%s" % (l))
