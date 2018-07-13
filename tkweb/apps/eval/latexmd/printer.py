import io
import os
import re
import functools
import contextlib
import unicodedata

from .document import Container, DocListItem, DocSection, Document

FILE_EXTENSION = '.md'


class FileStructure:
    def __init__(self, level):
        self.level = level

    def is_leaf(self, node):
        return node.level >= self.level


class MarkdownPrinter:
    def __init__(self):
        self.section_parents = []

    def print(self, v, end=None):
        print(v, end=end)

    def visit(self, arg):
        try:
            method = getattr(self, 'visit_' + arg.__class__.__name__)
        except AttributeError:
            method = self.generic_visit
        return method(arg)

    def generic_visit(self, node):
        if not isinstance(node, Container):
            raise TypeError(node)
        for v in node:
            self.visit(v)

    def visit_str(self, node):
        self.print(node, end='')

    def visit_Preamble(self, node):
        pass

    @contextlib.contextmanager
    def capture(self):
        buf = io.StringIO()
        with self.wrap_print(functools.partial(print, file=buf)):
            yield buf

    @contextlib.contextmanager
    def wrap_print(self, fn):
        prev, self.print = self.print, fn
        try:
            yield
        finally:
            self.print = prev

    def print_markdown_header(self, markdown_level, name):
        assert markdown_level >= 0
        if markdown_level == 0:
            self.print(name)
            self.print('=' * len(name))
        elif markdown_level == 1:
            self.print(name)
            self.print('-' * len(name))
        else:
            self.print('#' * markdown_level + ' ' + name)

    def visit_DocSection(self, node):
        with self.capture() as namebuf:
            self.visit(node.name)
        name = namebuf.getvalue()
        while self.section_parents and self.section_parents[-1].level >= node.level:
            self.section_parents.pop()
        markdown_level = len(self.section_parents)
        self.section_parents.append(node)
        self.print('')
        self.print_markdown_header(markdown_level, name)
        self.generic_visit(node)
        self.print('')

    def visit_DocPostamble(self, node):
        pass

    list_depth = 0

    def visit_DocList(self, node):
        if self.list_depth == 0:
            self.print('')
        self.list_depth += 1
        for v in node:
            if isinstance(v, DocListItem):
                with self.capture() as itembuf:
                    self.visit(v)
                item = itembuf.getvalue().strip()
                first_indent = '* ' * self.list_depth
                indent = '  ' * self.list_depth
                self.print(first_indent + item.replace('\n', '\n' + indent))
        self.list_depth -= 1

    def visit_DocReference(self, node):
        target = node.target.target
        # TODO link
        self.print('[', end='')
        if isinstance(target, DocSection):
            self.visit(target.name)
        else:
            self.print('ref', end='')
        link = 'LINK TODO'
        self.print('](%s)' % link, end='')

    def visit_DocAnonBreak(self, node):
        self.print('\n-----\n')

    def visit_DocVerbatim(self, node):
        self.print('`%s`' % node.args[0], end='')

    def visit_DocFormatted(self, node):
        with self.capture() as buf:
            self.visit(node.args[1])
        contents = buf.getvalue()
        assert isinstance(contents, str), repr(contents)
        if node.args[0] == 'emph':
            self.print('*%s*' % contents, end='')
        elif node.args[0] == 'paragraph':
            self.print('\n\n**%s**' % contents, end='')
        elif node.args[0] == 'textbf':
            self.print('**%s**' % contents, end='')
        elif node.args[0] == 'textsc':
            # TODO
            self.print(contents.upper(), end='')
        elif node.args[0] == 'textit':
            self.print('*%s*' % contents, end='')
        elif node.args[0] == 'texttt':
            self.print('`%s`' % contents, end='')
        elif node.args[0] == 'url':
            self.print('<%s>' % contents, end='')
        elif node.args[0] == 'TKprefix':
            self.print('[tk_prefix %s]' % contents, end='')
        elif node.args[0] == 'KTKprefix':
            self.print('[tk_kprefix %s]' % contents, end='')
        else:
            raise ValueError(node.args[0])

    def visit_DocFixme(self, node):
        self.print('')
        self.print('!!! note')
        with self.capture() as buf:
            self.visit(node.args[1])
        self.print('    ' + buf.getvalue().strip().replace('\n', '\n    '))
        self.print('')

    def visit_DocFootnote(self, node):
        self.print('(Fodnote: ', end='')
        self.visit(node.args[1])
        self.print(' --slut fodnote)', end='')

    def visit_DocAbbreviation(self, node):
        if node.args[0] in ('TK', 'TKET', 'TKETAA'):
            self.print('[%s%s]' % (node.args[0], node.args[1]), end='')
        else:
            self.print(node.to_list(), end='')

    def visit_DocSpacing(self, node):
        pass


def to_markdown(node, **kwargs):
    assert 'level' not in kwargs
    printer = MarkdownPrinter(**kwargs)
    with printer.capture() as buf:
        printer.visit(node)
    return buf.getvalue()


class ResolveLinks:
    HEADER_ID_PREFIX = "wiki-toc-"
    IDCOUNT_RE = re.compile(r'^(.*)_([0-9]+)$')
    MAX_LENGTH = 48

    @staticmethod
    def slugify(value, separator):
        """ Slugify a string, to make it URL friendly. """
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
        value = re.sub('[^\w\s-]', '', value.decode('ascii')).strip().lower()
        return re.sub('[%s\s]+' % separator, separator, value)

    @staticmethod
    def unique(elem_id, ids):
        """ Ensure id is unique in set of ids. Append '_1', '_2'... if not """
        while elem_id in ids:
            m = ResolveLinks.IDCOUNT_RE.match(elem_id)
            if m:
                elem_id = '%s_%d' % (m.group(1), int(m.group(2)) + 1)
            else:
                elem_id = '%s_%d' % (elem_id, 1)
        ids.add(elem_id)
        return elem_id

    def __init__(self, file_structure: FileStructure):
        self.file_structure = file_structure
        # Map id(DocSection) to a HREF
        self.links = {}
        self.current_path = []
        # Map id(s: DocSection where s is non-leaf) to set of child
        # section names, and id(s: DocSection where s is leaf)
        # to set of anchor names (without HEADER_ID_PREFIX prefix)
        self.child_name_set = {}
        self.children = {}

    def is_leaf(self, node):
        return self.file_structure.is_leaf(node)

    def create_child_name(self, parent: DocSection, child_title):
        slug = self.slugify(child_title, '-')[:self.MAX_LENGTH]
        if self.is_leaf(parent):
            # django-wiki decides the name of this child
            used_ids = self.child_name_set.setdefault(id(parent), set())
            return self.unique(slug, used_ids)
        else:
            # We get to decide the name of this child
            used_ids = self.child_name_set.setdefault(id(parent), set())
            return self.unique(slug, used_ids)

    def visit(self, arg):
        try:
            method = getattr(self, 'visit_' + arg.__class__.__name__)
        except AttributeError:
            method = self.generic_visit
        return method(arg)

    def visit_str(self, arg):
        pass

    def generic_visit(self, node):
        if not isinstance(node, Container):
            raise TypeError(node.__class__)
        for v in node:
            self.visit(v)

    def initial_visit(self, node, path):
        assert isinstance(node, Document)
        assert self.current_path == []
        assert path.startswith('/')
        self.current_path.append(node)
        self.links[id(node)] = path
        self.child_name_set[id(node)] = set()
        self.children[id(node)] = []
        self.generic_visit(node)
        assert self.current_path == [node]
        self.current_path.pop()

    def visit_Document(self, node):
        raise Exception('Unexpected Document')

    def visit_DocSection(self, node):
        parent = self.current_path[-1]
        parent_path = self.links[id(parent)]
        my_title = to_markdown(node.name)
        my_name = self.create_child_name(parent, my_title)
        self.children.setdefault(id(parent), []).append((my_name, node))
        if self.is_leaf(parent):
            my_path = '%s/#%s%s' % (parent_path, self.HEADER_ID_PREFIX, my_name)
            self.links[id(node)] = my_path
            self.generic_visit(node)
        else:
            my_path = os.path.join(parent_path, my_name)
            self.links[id(node)] = my_path
            self.current_path.append(node)
            self.generic_visit(node)
            assert self.current_path[-1] is node
            self.current_path.pop()


class DirectoryWriter(MarkdownPrinter):
    def __init__(self, file_structure: FileStructure, base):
        if not base.endswith(FILE_EXTENSION):
            raise ValueError(base)
        super().__init__()
        self.file_structure = file_structure
        self.current_file = None
        self.current_children = None
        self.current_link = None
        self.base = base[:-len(FILE_EXTENSION)]
        self.base_dir = os.path.dirname(self.base)
        self.links = ResolveLinks(file_structure)
        self.in_leaf = False

    def __enter__(self):
        return self

    def __exit__(self, exc, exv, ext):
        if self.current_file is not None:
            self.close_current_file()

    def is_leaf(self, node):
        return self.file_structure.is_leaf(node)

    def print(self, v, end=None):
        if self.current_file is not None:
            if self.first_line and not v:
                return
            self.first_line = False
            print(v, end=end, file=self.current_file)

    def close_current_file(self):
        if self.current_children:
            self.print('\n\nUndersider:\n')
            for name, node in self.current_children:
                self.print('* [%s](%s)' % (to_markdown(node.name), name))
        self.current_file.flush()
        self.current_file.close()
        self.current_file = None

    def set_filename(self, path):
        if self.current_file is not None:
            self.close_current_file()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.current_file = open(path, 'w')
        self.first_line = True
        self.has_emitted_toc = False

    def visit_Document(self, node):
        path = self.base
        slug = os.path.basename(path)
        self.links.initial_visit(node, '/' + slug)
        self.set_filename(path + FILE_EXTENSION)
        self.set_current_children(node)
        self.current_link = self.links.links[id(node)]
        self.print_markdown_header(0, slug[0].upper() + slug[1:])
        self.generic_visit(node)

    def set_current_children(self, node):
        self.current_children = (
            () if self.is_leaf(node) else
            self.links.children.get(id(node), ()))

    def visit_DocSection(self, node):
        link = self.links.links[id(node)]
        if self.in_leaf:
            if not self.has_emitted_toc:
                self.has_emitted_toc = True
                self.print('\n[TOC]\n')
            super().visit_DocSection(node)
        else:
            self.in_leaf = self.is_leaf(node)
            assert link.startswith('/')
            assert '#' not in link
            path = os.path.join(self.base_dir, link[1:])
            self.set_filename(path + FILE_EXTENSION)
            self.set_current_children(node)
            self.current_link = link
            with self.capture() as namebuf:
                self.visit(node.name)
            self.print_markdown_header(0, namebuf.getvalue())
            self.print('')
            self.generic_visit(node)
            self.in_leaf = False

    def visit_DocReference(self, node):
        target = node.target.target
        if isinstance(target, DocSection):
            self.print('[', end='')
            self.visit(target.name)
            link = self.links.links[id(target)]
            rel_link = os.path.relpath(link, self.current_link)
            self.print('](%s)' % rel_link, end='')
        else:
            self.print('?ref', end='')
