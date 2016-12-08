import subprocess

from django.core.exceptions import ValidationError


def file_for_subprocess(file):
    file.open('rb')
    try:
        file.fileno()
    except Exception:
        stdin = subprocess.PIPE
        comm_args = (file.read(),)
    else:
        stdin = file
        comm_args = ()
    return file, stdin, comm_args


def extract_plain_text(file):
    file, stdin, comm_args = file_for_subprocess(file)
    proc = subprocess.Popen(
        ('pdftotext', '-', '-'),
        stdin=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdoutbytes, stderrbytes = proc.communicate(*comm_args)
    stdout = stdoutbytes.decode()
    stderr = stderrbytes.decode()
    if proc.returncode == 1:
        raise ValidationError("Du skal uploade en PDF-fil")
    elif proc.returncode != 0:
        stderr_brief = stderr[:100]
        raise ValidationError("pdftotext fejlede: %s" % stderr_brief)
    return stdout


def get_pdfinfo(file):
    file, stdin, comm_args = file_for_subprocess(file)
    proc = subprocess.Popen(
        ('pdfinfo', '-'),
        stdin=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdoutbytes, stderrbytes = proc.communicate(*comm_args)
    stdout = stdoutbytes.decode()
    stderr = stderrbytes.decode()
    if proc.returncode == 1:
        raise ValidationError("Du skal uploade en PDF-fil")
    elif proc.returncode != 0:
        stderr_brief = stderr[:100]
        raise ValidationError("pdfinfo fejlede: %s" % stderr_brief)
    return stdout


def pages_from_pdfinfo(text):
    try:
        line, = (l for l in text.splitlines() if l.startswith('Pages:'))
        return int(line.split()[1])
    except Exception:
        raise Exception("Could not parse pdfinfo: %r" % (text,))
