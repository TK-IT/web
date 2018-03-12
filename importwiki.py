#!/usr/bin/env python
import os
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('root', nargs='+')


MD_EXTENSION = '.md'


def find_files(filenames):
    def rec(base, f):
        d = f[:-len(MD_EXTENSION)]
        yield d, os.path.join(base, f)
        try:
            path = os.path.join(base, d)
            cs = os.listdir(path)
        except FileNotFoundError:
            # print('Skip nonexistent', path)
            return
        # print('Recurse', path, cs)
        for c in cs:
            if c.endswith(MD_EXTENSION):
                yield from rec(base, os.path.join(d, c))

    for f in filenames:
        assert os.path.exists(f)
        assert f.endswith(MD_EXTENSION)
        yield from rec(os.path.dirname(f), os.path.basename(f))


def read_contents(files):
    seen = {''}
    for path, file in files:
        # print(path, file)
        parent = os.path.dirname(path)
        assert parent in seen
        seen.add(path)
        with open(file) as fp:
            title = next(fp, None).strip('\n')
            sep = next(fp, None).strip('\n')
            assert sep and sep == '=' * len(sep), file
            content = fp.read().strip()
        # print(parent, os.path.basename(path), title)
        yield path, parent, title, content


def main():
    args = parser.parse_args()
    for r in args.root:
        if not r.endswith(MD_EXTENSION):
            parser.error('Must end with %s: %r' % (MD_EXTENSION, r))

    files = list(find_files(args.root))
    contents = list(read_contents(files))

    from wiki.models import Article, ArticleRevision, URLPath

    paths = {'': URLPath.create_root()}
    for path, parent, title, content in contents:
        parent_urlpath = paths[parent]
        paths[path] = URLPath.create_urlpath(
            parent=parent_urlpath,
            slug=os.path.basename(path),
            site=parent_urlpath.site,
            title=title,
            content=content,
        )


if __name__ == "__main__":
    import django
    django.setup()
    main()