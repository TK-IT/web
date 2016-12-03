import os
import tempfile
import subprocess
from django.conf import settings


class RenderError(subprocess.CalledProcessError):
    pass


def tex_to_pdf(source, jobname='django'):
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, jobname)
        with open(base + '.tex', 'w', encoding='utf8') as fp:
            fp.write(source)
        cmd = ('pdflatex', base + '.tex')
        p = subprocess.Popen(
            cmd,
            cwd=d,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True)
        with p:
            output, _ = p.communicate()
        if p.returncode != 0:
            raise RenderError(p.returncode, cmd, output, stderr=None)
        with open(base + '.pdf', 'rb') as fp:
            return fp.read()


def pdfnup(pdf, jobname='django'):
    with tempfile.TemporaryDirectory() as d:
        base = os.path.join(d, jobname)
        out = base + '-nup'
        with open(base + '.pdf', 'w', encoding='utf8') as fp:
            fp.write(source)
        cmd = ('pdfnup', base + '.pdf', '-o', out + '.pdf')
        p = subprocess.Popen(
            cmd,
            cwd=d,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True)
        with p:
            output, _ = p.communicate()
        if p.returncode != 0:
            raise RenderError(p.returncode, cmd, output, stderr=None)
        with open(out + '.pdf', 'rb') as fp:
            return fp.read()


def run_lp(pdf, duplex=True, hostname=None, destination=None):
    if hostname is None:
        hostname = getattr(settings, 'CUPS_HOSTNAME', 'localhost')
    if destination is None:
        destination = settings.PRINT_DESTINATION
    with tempfile.NamedTemporaryFile(mode='wb') as fp:
        fp.write(pdf)
        cmd = ('lp', '-h', hostname, '-d', destination, fp.name)
        p = subprocess.Popen(
            cmd,
            cwd=d,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True)
        with p:
            output, _ = p.communicate()
        if p.returncode != 0:
            raise RenderError(p.returncode, cmd, output, stderr=None)
    return output
