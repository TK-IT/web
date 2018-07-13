#!/bin/bash

if [ $# -gt 0 ]; then
	cat <<EOF
Usage: PYTHONPATH=. tools/latex-to-markdown.sh

Run tkweb.apps.eval.latexmd to convert a set of LaTeX source files in evalsrc/
to Markdown files in evalmd/. The output files are suitable for use with
tools/import-markdown.py.
EOF
	exit 1
fi
set -euo pipefail
rm -rf evalmd
python -m tkweb.apps.eval.latexmd -o "evalmd/besteval.md" "evalsrc/besteval/besteval.tex" -l besteval
python -m tkweb.apps.eval.latexmd -o "evalmd/formeval.md" "evalsrc/formeval/main.tex" -l chapter
python -m tkweb.apps.eval.latexmd -o "evalmd/kass.md" "evalsrc/kass/KASSs VISKASS.tex" -l chapter
python -m tkweb.apps.eval.latexmd -o "evalmd/vc.md" "evalsrc/vc/besteval.tex" -l chapter
python -m tkweb.apps.eval.latexmd -o "evalmd/nf.md" "evalsrc/nf/PROPAGANDA.tex" -l section
python -m tkweb.apps.eval.latexmd -o "evalmd/cerm.md" "evalsrc/cerm/CIRKUS1718.tex" -l chapter
