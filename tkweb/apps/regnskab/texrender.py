import os
import tempfile
import subprocess
from django.conf import settings


class RenderError(subprocess.CalledProcessError):
    pass


def tex_to_pdf(source, jobname="django"):
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, jobname)
        with open(base + ".tex", "w", encoding="utf8") as fp:
            fp.write(source)
        cmd = ("pdflatex", base + ".tex")
        p = subprocess.Popen(
            cmd,
            cwd=d,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        with p:
            output, _ = p.communicate()
        if p.returncode != 0:
            raise RenderError(p.returncode, cmd, output, stderr=None)
        with open(base + ".pdf", "rb") as fp:
            return fp.read()


def pdfnup(pdf, jobname="django"):
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, jobname)
        out = base + "-nup"
        with open(base + ".pdf", "wb") as fp:
            fp.write(pdf)
        cmd = ("pdfnup", base + ".pdf", "-o", out + ".pdf")
        p = subprocess.Popen(
            cmd,
            cwd=d,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        with p:
            output, _ = p.communicate()
        if p.returncode != 0:
            raise RenderError(p.returncode, cmd, output, stderr=None)
        with open(out + ".pdf", "rb") as fp:
            return fp.read()


def run_lp(pdf, duplex=True, hostname=None, destination=None):
    if hostname is None:
        hostname = getattr(settings, "CUPS_HOSTNAME", "localhost")
    if destination is None:
        destination = settings.PRINT_DESTINATION
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf") as fp:
        fp.write(pdf)
        if duplex:
            opt = ("-o", "Duplex=DuplexNoTumble")
        else:
            opt = ("-o", "Duplex=None")

        cmd = ("lp", "-h", hostname, "-d", destination) + opt + (fp.name,)
        p = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(fp.name),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        with p:
            output, _ = p.communicate()
        if p.returncode != 0:
            raise RenderError(p.returncode, cmd, output, stderr=None)
    return output


def print_new_document(fp, filename, username, **kwargs):
    """Drop-in replacement for uniprint.api.print_new_document"""
    duplex = kwargs.pop("duplex", True)
    printer = kwargs.pop("printer")
    fake = kwargs.pop("fake", None)
    copies = kwargs.pop("copies", 1)
    if copies != 1:
        raise ValueError("can only print 1 copy at a time")
    if kwargs:
        raise TypeError("unsupported kwargs: %s" % kwargs)
    if not fake:
        run_lp(fp.read(), duplex=duplex)
