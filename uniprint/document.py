import subprocess

from django.core.exceptions import ValidationError


class FileTypeError(Exception):
    pass


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


def run_poppler(file, *args):
    '''
    Run a command from the poppler utility distribution.
    '''
    file, stdin, comm_args = file_for_subprocess(file)
    proc = subprocess.Popen(
        args,
        stdin=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdoutbytes, stderrbytes = proc.communicate(*comm_args)
    stdout = stdoutbytes.decode()
    stderr = stderrbytes.decode()
    # Poppler util returns 0 on success and 1 on invalid input
    if proc.returncode == 1:
        raise FileTypeError()
    elif proc.returncode != 0:
        # Internal/other error
        stderr_brief = stderr[:100]
        raise subprocess.CalledProcessError(
            proc.returncode, proc.args, stdout, stderr)
    return stdout


def extract_plain_text(file):
    return run_poppler(file, 'pdftotext', '-', '-')


def get_pdfinfo(file):
    return run_poppler(file, 'pdfinfo', '-')


def pages_from_pdfinfo(text):
    try:
        line, = (l for l in text.splitlines() if l.startswith('Pages:'))
        return int(line.split()[1])
    except Exception:
        raise Exception("Could not parse pdfinfo: %r" % (text,))
