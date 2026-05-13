#!/usr/bin/env bash
# Regenera el PDF de la memoria académica desde la fuente LaTeX.
set -euo pipefail

cd "$(dirname "$0")/informe"
pdflatex -interaction=nonstopmode informe_academico.tex
pdflatex -interaction=nonstopmode informe_academico.tex  # segunda pasada para referencias cruzadas

echo ""
echo "PDF generado: informe/informe_academico.pdf"
