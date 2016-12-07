from django.db import models


class Document(models.Model):
    file = models.FileField()
    pages = models.IntegerField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField()


class Printer(models.Model):
    name = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)

    @property
    def hostname(self):
        return 'localhost'

    @property
    def port(self):
        return 6631


class Printout(models.Model):
    document = models.ForeignKey(Document, on_delete=models.SET_NULL,
                                 null=True, blank=False)
    printer = models.ForeignKey(Printer, on_delete=models.SET_NULL,
                                null=True, blank=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                   null=True, blank=False)
    created_time = models.DateTimeField()

    duplex = models.BooleanField(blank=True)

    def send_to_printer(self):
        with self.document.file.open('rb') as fp:
            pdf = fp.read()
        host = '%s:%s' % (self.printer.hostname, self.printer.port)
        destination = self.printer.destination
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf') as fp:
            fp.write(pdf)
            if self.duplex:
                opt = ('-o', 'Duplex=DuplexNoTumble')
            else:
                opt = ('-o', 'Duplex=None')

            cmd = ('lp', '-h', host, '-d', destination) + opt + (fp.name,)
            p = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(fp.name),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True)
            with p:
                output, _ = p.communicate()
            if p.returncode != 0:
                raise RenderError(p.returncode, cmd, output, stderr=None)
        return output
