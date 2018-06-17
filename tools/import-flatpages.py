#!/usr/bin/env python

"""
Import flatpages views from TAAGEKAMMERET.dk
"""

import argparse

try:
    import requests
except ImportError:
    raise SystemExit("Please install the requests package")

try:
    import html5lib
except ImportError:
    raise SystemExit("Please install the html5lib package")


def get_flatpages(urlpatterns):
    for entry in urlpatterns:
        if entry.callback == flatpage:
            yield entry
        if hasattr(entry, "url_patterns"):
            yield from get_flatpages(entry.url_patterns)


parser = argparse.ArgumentParser(
    description=__doc__.strip(), formatter_class=argparse.RawDescriptionHelpFormatter
)


def main():
    parser.parse_args()  # Handle --help
    prefix = "https://TAAGEKAMMERET.dk"

    flatpages = get_flatpages(urls.urlpatterns)
    for p in flatpages:
        url = p.default_args["url"]
        absurl = prefix + url
        r = requests.get(absurl)
        if r.status_code != 200:
            print("Failed to GET %s" % absurl)
            continue

        doc = html5lib.parse(r.content)
        bodyels = doc.findall('.//*[@role="main"]/*')
        title = "".join(bodyels[0].itertext()).strip()

        # Remove header and footer
        bodyels = bodyels[1:-1]

        flathtml = "".join(map(html5lib.serialize, bodyels))

        f, created = FlatPage.objects.update_or_create(
            url=url, defaults=dict(title=title, content=flathtml)
        )
        if created:
            FlatPage.sites.through.objects.create(flatpage=f, site_id=1)

        print("Imported flatpage %s" % url)


if __name__ == "__main__":
    import django

    django.setup()

    from django.core.management.base import BaseCommand, CommandError
    from django.contrib.flatpages.views import flatpage
    from django.contrib.flatpages.models import FlatPage
    from tkweb import urls

    main()
