import io
import base64
import tempfile
import subprocess

import numpy as np
import imageio
import PIL


def imagemagick_page_count(filename):
    """
    Get the number of pages in a named TIFF or PDF file.
    """
    cmdline = ('identify', filename)
    p = subprocess.Popen(
        cmdline, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
        universal_newlines=True)
    with p:
        stdout, stderr = p.communicate()
    # The number of pages is just the number of lines in the output.
    return len(stdout.splitlines())


def load_tiff_page(filename, page):
    """
    Try to load a particular page from a TIFF image file.
    """
    im = PIL.Image.open(filename)
    try:
        im.seek(page)
    except EOFError:
        return None
    bw = False
    if im.mode == "YCbCr" and not bw:
        im = im.convert('RGB')
    a = scipy.misc.fromimage(im, flatten=bw)
    if not bw and a.ndim == 2:
        a = a[:, :, np.newaxis]
        a = np.repeat(a, 3, axis=2)
    return a / 255.0


def load_pdf_page(filename: str, page: int) -> np.ndarray:
    # convert -density 150 '2221_001.pdf[0]' 2221_001_1.png
    with tempfile.NamedTemporaryFile(suffix='.ppm') as fp:
        subprocess.check_call(
            ('convert', '-density', '150', '-depth', '8',
             # '-background', 'white', '-alpha', 'remove',
             '%s[%s]' % (filename, page),
             fp.name))
        img = np.asarray(imageio.imread(fp.name))

    return img / 255.0


def save_png(im_array):
    if im_array.dtype == np.float64:
        im_array = (im_array * 255).astype(np.uint8)
    img = PIL.Image.fromarray(im_array)
    output = io.BytesIO()
    img.save(output, 'PNG')
    return output.getvalue()


def png_data_uri(png_data):
    png_b64 = base64.b64encode(png_data).decode()
    return 'data:image/png;base64,%s' % png_b64
