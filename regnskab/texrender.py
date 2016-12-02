import os
import tempfile
import subprocess


class RenderError(subprocess.CalledProcessError):
    pass


def tex_to_pdf(source):
    with tempfile.TemporaryDirectory() as d:
        jobname = 'plans'
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
