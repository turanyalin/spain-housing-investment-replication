# Manuscript figures

`figure1.pdf` shows indexed real house prices and manufacturing investment, followed by annual growth rates. `figure2.pdf` shows the partial relationship between house-price and manufacturing investment growth after removing GDP growth and the 2020 indicator.

Regenerate both vector PDFs with `python reproduce.py` from the repository root. Corresponding PNG files are written to `replication/figure1.png` and `replication/figure2.png`. `main.tex` embeds the PDFs directly. No external images or proprietary fonts are required.

Figure bytes can differ across runs because of rendering metadata or platform differences. Numerical results are checked separately by the reproduction command.
