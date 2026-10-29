.PHONY: reproduce paper clean

PYTHON ?= python

reproduce:
	$(PYTHON) reproduce.py

paper:
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

clean:
	latexmk -c main.tex
