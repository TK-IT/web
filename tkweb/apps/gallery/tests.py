from PIL import Image as PILImage
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from tkweb.apps.gallery.models import Album, Image
import tempfile


class SimpleAlbumTest(TestCase):
    def test_empty_album(self):
        self.assertFalse(Album.objects.exists())
        instance = Album.objects.create(title="Album Title", slug="album-title")
        instance.full_clean()
        self.assertTrue(Album.objects.exists())


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class SimpleMediaTest(TestCase):
    def setUp(self):
        album = Album.objects.create(title="Album Title", slug="album-title")
        album.full_clean()

    def generate_image(self, suffix):
        album = Album.objects.all()[0]

        temp_file = tempfile.NamedTemporaryFile(suffix=suffix)
        PILImage.new("RGB", (100, 100)).save(temp_file)

        Image(file=temp_file.name, album=album).save()

        try:
            Image.objects.all()[0].file.crop["200x200"]
        except ValidationError:
            self.fail(
                "VersatileImageField Raised ValidationError on a good %s image" % suffix
            )
        self.assertEqual(len(Image.objects.all()), 1)
        self.assertIsInstance(album.basemedia.select_subclasses()[0], Image)

    def test_simple_jpg_album(self):
        self.generate_image(".jpg")

    def test_simple_png_album(self):
        self.generate_image(".png")

    def test_simple_gif_album(self):
        self.generate_image(".gif")
