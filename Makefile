.PHONY: reproduce test paper clean

PYTHON ?= python

reproduce:
	$(PYTHON) reproduce.py

test:
	$(PYTHON) -m unittest discover -s tests -v

paper: reproduce
	latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex

clean:
	latexmk -c main.tex
