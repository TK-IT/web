import io
import os
import re
import argparse
import functools
import contextlib
import collections
import unicodedata

from . import texparse
from .texparse import get_contents_autotex, UNMATCHED
from .document import (
    Container, Root, Preamble, Standalone, Document, DocSection, DocPostamble,
    DocListItem, DocList, DocBraced, Leaf, Label, DocReference, DocAnonBreak,
    DocFormatted, DocFixme, DocFootnote, DocAbbreviation, DocSpacing,
    DocVerbatim,
)

from .printer import (
    FILE_EXTENSION, to_markdown, DirectoryWriter, FileStructure,
)


MAIN = 'main'
SUBFILE = 'subfile'
INCLUDE = 'include'

LEVELS = 'part chapter section subsection subsubsection'.split()


def parse(base, main_file, *, labels=None):
    # TODO factor out besteval specifics: checklist, abbreviations, TKprefix
    list_kinds = 'itemize enumerate description checklist'.split()
    patterns = [
        ('begindoc', r'\\begin{document}'),
        ('enddoc', r'\\end{document}'),
        ('header', r'\\((?:eval)?)(%s)\b(\*?)' % '|'.join(LEVELS)),
        ('label', r'\\label{([^{}]*)}'),
        ('ref', r'\\(ref|vref|fref|nameref|pageref|Cref)(\*?){([^{}]*)}'),
        ('beginlist', r'\\begin{(%s)}' % '|'.join(list_kinds)),
        ('endlist', r'\\end{(%s)}' % '|'.join(list_kinds)),
        ('item', r'\\item\b'),
        ('subfile', r'\\subfile{([^}]*)}'),
        ('include', r'\\include{([^}]*)}'),
        ('anonbreak', r'\\(anonbreak\b|plainbreak\d+|plainbreak{}|starbreak)'),
        ('formatted', r'\\(emph|paragraph|textbf|textsc|textit|texttt|url|TKprefix|KTKprefix)\b'),
        ('verb', r'\\verb\|([^|]*)\|'),
        ('fixme', r'\\(fxnote)\b'),
        ('footnote', r'\\(footnote)\b'),
        ('abbreviation', r'\\(TKET|TKETAA|TK|KASS|CERM|VC|TKurl)([Ss]?)(?:pdf)?\b'),
        ('brace', r'[{}]'),
        ('dots', r'\\dots\b'),
        ('quotemark', r'(``|\'\'|"`|"\'|`|\')'),
        ('hardnewline', r'\\\\'),
        ('guidedata', r'\\guide(title|label|author|date)\b'),
        ('makeguidetitle', r'\\makeguidetitle\b'),
        ('texspacing', r'\\((?:noindent|newpage|clearpage|cleardoublepage|vfill|tableofcontents|mainmatter|firkant)\b|thispagestyle{[^{}]*})'),
    ]

    def get_contents(filename):
        return get_contents_autotex(os.path.join(base, filename))

    stack = [Root(), Preamble()]
    stack[0].append(stack[1])
    subfile_depth = 0

    if labels is None:
        labels = collections.defaultdict(Label)

    parser = texparse.parse(patterns, main_file, get_contents)
    pending_brace = None
    guidedata = {}

    for key, values in parser:
        in_preamble = len(stack) >= 2 and isinstance(stack[1], Preamble)
        if pending_brace:
            assert ((key == UNMATCHED and not values[0].strip()) or
                    key == 'brace'), stack
        if key == UNMATCHED:
            v, = values
            stack[-1].append(re.sub(r' *\n *', '\n', v))
        elif key == 'begindoc':
            if subfile_depth == 0:
                assert isinstance(stack[1], Preamble)
                stack[-1] = Document()
                stack[-2].append(stack[-1])
        elif key == 'enddoc':
            if subfile_depth == 0:
                while isinstance(stack[-1], DocSection):
                    stack.pop()
                assert isinstance(stack[-1], Document)
                stack[-1] = DocPostamble()
                stack[-2].append(stack[-1])
        elif key == 'beginsubfile':
            subfile_depth += 1
        elif key == 'endsubfile':
            assert subfile_depth > 0
            subfile_depth -= 1
        elif key == 'header':
            full_text, eval_vary, level_name, star = values
            if in_preamble:
                # Essentially ignore this since besteval does some
                # magic involving \chapter, \section, \subsection
                stack[-1].append(full_text)
            else:
                level = LEVELS.index(level_name)
                # Ignore eval_vary (only used in kbesteval)
                pending_brace = DocBraced()
                assert isinstance(stack[-1], (Standalone, DocSection)), stack
                while stack[-1].level >= level:
                    stack.pop()
                c = DocSection(level, pending_brace, star)
                stack[-1].append(c)
                stack.append(c)
        elif key == 'label':
            _, v = values
            l = labels[v]
            if l.target is not None:
                print('Warning: Redefining label', v)
            l.target = stack[-1]
        elif key == 'ref':
            _, kind, star, v = values
            stack[-1].append(DocReference(kind, labels[v]))
        elif key == 'beginlist':
            full_text, kind = values
            if in_preamble:
                stack[-1].append(full_text)
            else:
                l = DocList(kind)
                stack[-1].append(l)
                stack.append(l)
                stack.append(l.preamble)
        elif key == 'item':
            if in_preamble:
                stack[-1].append(values[0])
            else:
                assert isinstance(stack[-2], DocList), stack
                stack[-1] = DocListItem()
                stack[-2].append(stack[-1])
        elif key == 'endlist':
            full_text, kind = values
            if in_preamble:
                stack[-1].append(full_text)
            else:
                assert isinstance(stack[-2], DocList), stack
                assert stack[-2].kind == kind, stack[-2].kind
                stack.pop()
                stack.pop()
        elif key == 'subfile':
            _, v = values
            parser.push_synthetic([('endsubfile', ('',))])
            parser.push_file(v)
            parser.push_synthetic([('beginsubfile', ('',))])
        elif key == 'include':
            _, v = values
            parser.push_file(v)
        elif key == 'anonbreak':
            stack[-1].append(DocAnonBreak())
        elif key == 'formatted':
            full_text, kind = values
            if in_preamble:
                stack[-1].append(full_text)
            else:
                pending_brace = DocBraced()
                stack[-1].append(DocFormatted(kind, pending_brace))
        elif key == 'verb':
            full_text, contents = values
            if in_preamble:
                stack[-1].append(full_text)
            else:
                stack[-1].append(DocVerbatim(contents))
        elif key == 'fixme':
            full_text, kind = values
            if in_preamble:
                stack[-1].append(full_text)
            else:
                pending_brace = DocBraced()
                stack[-1].append(DocFixme(kind, pending_brace))
        elif key == 'footnote':
            full_text, kind = values
            if in_preamble:
                stack[-1].append(full_text)
            else:
                pending_brace = DocBraced()
                stack[-1].append(DocFootnote(kind, pending_brace))
        elif key == 'abbreviation':
            full_text, kind, s = values
            if in_preamble:
                stack[-1].append(full_text)
            else:
                stack[-1].append(DocAbbreviation(kind, s))
        elif key == 'brace':
            kind, = values
            if kind == '{':
                if pending_brace:
                    stack.append(pending_brace)
                    pending_brace = None
                else:
                    stack.append(DocBraced())
                    stack[-2].append(stack[-1])
            else:
                assert kind == '}'
                if isinstance(stack[-1], DocBraced):
                    stack.pop()
                else:
                    print('Warning: Unmatched close brace')
                    stack[-1].append(kind)
        elif key == 'dots':
            stack[-1].append(DocAbbreviation('dots', ''))
        elif key == 'quotemark':
            stack[-1].append(DocAbbreviation(values[0], ''))
        elif key == 'hardnewline':
            stack[-1].append(DocAbbreviation(values[0], ''))
        elif key == 'guidedata':
            full_text, key = values
            if in_preamble:
                stack[-1].append(full_text)
            else:
                pending_brace = DocBraced()
                guidedata[key] = pending_brace
        elif key == 'makeguidetitle':
            full_text, = values
            if in_preamble:
                # Essentially ignore this since besteval does some magic.
                stack[-1].append(full_text)
            else:
                level_name = 'chapter'
                level = LEVELS.index(level_name)
                star = ''
                assert isinstance(stack[-1], (Standalone, DocSection)), stack
                while stack[-1].level >= level:
                    stack.pop()
                try:
                    title = guidedata.pop('title')
                except KeyError:
                    raise Exception('Guide has no title!')
                c = DocSection(level, title, star)
                c.is_guide = True
                stack[-1].append(c)
                stack.append(c)

                author = guidedata.pop('author', None)
                modified = guidedata.pop('date', None)
                label = guidedata.pop('label', None)
                if author is not None:
                    stack[-1].append('Af: ')
                    stack[-1].append(author)
                    stack[-1].append('\n\n')
                if modified is not None:
                    stack[-1].append('Sidst opdateret: ')
                    stack[-1].append(modified)
                    stack[-1].append('\n\n')
                if label is not None:
                    l = labels[label.to_list()]
                    if l.target is not None:
                        print('Warning: Redefining label', label.to_list())
                    l.target = stack[-1]
        elif key == 'texspacing':
            stack[-1].append(DocSpacing(values[0]))
        else:
            raise NotImplementedError(key)

    return stack[0]


parser = argparse.ArgumentParser()
parser.add_argument('-b', '--base-dir')
parser.add_argument('-o', '--output-root')
parser.add_argument('-l', '--level', default='section')
parser.add_argument('filename')


def main():
    args = parser.parse_args()
    if args.output_root and not args.output_root.endswith(FILE_EXTENSION):
        parser.error('Filename passed to -o must end with %s' %
                     FILE_EXTENSION)
    if not os.path.exists(args.filename):
        parser.error('No such file or directory: ' + args.filename)
    base_dir = args.base_dir
    if base_dir is None:
        base_dir = os.path.dirname(args.filename)
    filename = os.path.relpath(args.filename, base_dir)

    doc = parse(base_dir, filename)
    if args.output_root:
        if args.level == 'besteval':
            level = LEVELS.index('section')

            class BestevalFileStructure:
                def is_leaf(self, node):
                    return (node.level >= level or
                            getattr(node, 'is_guide', False))

            file_structure = BestevalFileStructure()
        else:
            file_structure = FileStructure(LEVELS.index(args.level))

        with DirectoryWriter(file_structure, args.output_root) as writer:
            writer.visit(doc)
    else:
        level = LEVELS.index(args.level)
        sections = list(doc.iter_sections(level))
        for s in sections:
            if isinstance(s, DocSection):
                print('%s %s %s' % (LEVELS[s.level], to_markdown(s.name), s.size()))
        # from pprint import pprint
        # pprint(doc.to_list())
        MarkdownPrinter().visit(doc)


if __name__ == '__main__':
    main()
