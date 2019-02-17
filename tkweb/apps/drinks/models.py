import os
import subprocess
import tempfile
from shutil import copyfile

from django.conf import settings
from django.core.files import File
from django.db import models


class Drink(models.Model):
    name = models.CharField(max_length=30)
    serving = models.CharField(max_length=50)
    price = models.IntegerField()
    secret = models.BooleanField()

    def __str__(self):
        return self.name


class Soda(models.Model):
    drink = models.ForeignKey(Drink, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class Sprut(models.Model):
    drink = models.ForeignKey(Drink, on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    amount = models.IntegerField()

    def __str__(self):
        return self.name


class Barcard(models.Model):
    name = models.CharField(max_length=30)
    drinks = models.ManyToManyField(Drink)
    barcard_file = models.FileField(blank=True, upload_to="barcard")
    mixing_file = models.FileField(blank=True, upload_to="mixing")
    source_file = models.FileField(blank=True, upload_to="source")

    def __str__(self):
        return self.name

    def generate_files(self):
        fp_src = os.path.join(os.path.dirname(__file__), "drinkskort")
        with tempfile.TemporaryDirectory(
            prefix="drinks", dir=settings.MEDIA_ROOT
        ) as temp_dir:

            # Copy source files to temp dir
            _, _, files = next(os.walk(fp_src))
            for sf in files:
                copyfile(os.path.join(fp_src, sf), os.path.join(temp_dir, sf))

            with open(os.path.join(temp_dir, "drinks.txt"), "w", encoding="utf8") as f:
                for drink in self.drinks.all():
                    secret = ""
                    if drink.secret:
                        secret = "?"
                    f.write("=%s %s\n" % (secret, drink.name))
                    for sprut in drink.sprut_set.all():
                        f.write("- %s cl - %s\n" % (sprut.amount, sprut.name))
                    for soda in drink.soda_set.all():
                        f.write("-- %s\n" % soda.name)
                    f.write("! %s\n" % drink.serving)
                    f.write("$ %s\n" % drink.price)
            env = dict(
                TEXMFVAR=os.path.join(temp_dir, "texmf-var"),
            )
            env.update(os.environ)
            result = subprocess.run(
                "make",
                shell=True,
                cwd=temp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=True,
                env=env,
            )
            with open(
                os.path.join(temp_dir, "bar_drinks.pdf"), mode="rb"
            ) as bar_file:
                self.barcard_file.save(self.name + "_barcard", File(bar_file))
            with open(
                os.path.join(temp_dir, "mixing_drinks.pdf"), mode="rb"
            ) as mix_file:
                self.mixing_file.save(self.name + "_mixing", File(mix_file))
            with open(
                os.path.join(temp_dir, "drinks.txt"), mode="r", encoding="utf8"
            ) as src_file:
                self.source_file.save(self.name + "_source", File(src_file))
