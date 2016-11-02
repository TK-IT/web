from django.core.management.base import BaseCommand, CommandError
from django.contrib.flatpages.views import flatpage
from django.contrib.flatpages.models import FlatPage
from tkweb import urls

def get_flatpages(urlpatterns):
    for entry in urlpatterns:
        if entry.callback == flatpage:
            yield entry
        if hasattr(entry, 'url_patterns'):
            yield from get_flatpages(entry.url_patterns)

class Command(BaseCommand):
	help = 'Import flatpages views from TAAGEKAMMERET.dk'

	def handle(self, *args, **options):
		prefix = 'http://TAAGEKAMMERET.dk'

		try:
			import requests
		except ImportError:
			raise CommandError('Please install the requests package')

		try:
			import html5lib
		except ImportError:
			raise CommandError('Please install the html5lib package')

		flatpages = get_flatpages(urls.urlpatterns)
		for p in flatpages:
			url = p.default_args['url']
			absurl = prefix + url
			r = requests.get(absurl)
			if r.status_code != 200:
				print('Failed to GET %s' % absurl)
				continue

			doc = html5lib.parse(r.content)
			bodyels = doc.findall('.//*[@role="main"]/*')
			title = ''.join(bodyels[0].itertext()).strip()

			# Remove header and footer
			bodyels = bodyels[1:-1]

			flathtml = ''.join(map(html5lib.serialize, bodyels))

			f = FlatPage.objects.create(
				url=url,
				title=title,
				content=flathtml
			)
			FlatPage.sites.through.objects.create(flatpage=f, site_id=1)

			print('Imported flatpage %s' % url)
