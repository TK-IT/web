import subprocess

from django.core.exceptions import ValidationError


def extract_plain_text(file):
    file.open('rb')
    try:
        file.fileno()
    except Exception:
        stdin = subprocess.PIPE
        comm_args = (file.read(),)
    else:
        stdin = file
        comm_args = ()
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
