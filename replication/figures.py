"""Generate the manuscript's two figures from observations and fitted models."""

from pathlib import Path
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _save_figure(figure, path: Path, **options):
    """Replace a completed image atomically so interrupted saves cannot truncate it."""
    temporary = path.with_name(path.stem + ".tmp" + path.suffix)
    try:
        figure.savefig(temporary, **options)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def make_figures(data, results, output_dir: Path):
    """Write PNG previews and vector PDFs using the same plotted observations."""
    (output_dir.parent / "figures").mkdir(parents=True, exist_ok=True)
    sample = data[data.year >= 1996]
    plt.rcParams.update(
        {
            "font.family": "DejaVu Serif",
            "font.size": 10,
            "pdf.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    fig, axs = plt.subplots(
        2, 1, figsize=(7.2, 6.0), sharex=True, gridspec_kw={"height_ratios": [1.15, 1]}
    )
    colors = {"house": "#4c667f", "manufacturing": "#171717", "equipment": "#777777"}
    for c, label in [
        ("house", "Real house prices"),
        ("manufacturing", "Manufacturing investment"),
        ("equipment", "Manufacturing equipment investment"),
    ]:
        axs[0].plot(
            data.year,
            100 * data[c] / data.loc[2000, c],
            label=label,
            color=colors[c],
            lw=1.8,
            ls="--" if c == "equipment" else "-",
        )
    axs[0].set_ylabel("Index 2000 = 100")
    axs[0].legend(frameon=False, fontsize=8, loc="upper left")
    axs[1].plot(
        data.year, data.g_house, color=colors["house"], label="House prices", lw=1.6
    )
    axs[1].plot(
        data.year,
        data.g_manufacturing,
        color=colors["manufacturing"],
        label="Manufacturing investment",
        lw=1.6,
    )
    axs[1].axhline(0, color="#999999", lw=0.6)
    axs[1].set_ylabel("Annual log growth × 100")
    axs[1].legend(frameon=False, fontsize=8)
    for ax in axs:
        ax.axvspan(2000, 2007, color="#c7d5e2", alpha=0.3)
        ax.axvspan(2008, 2013, color="#cccccc", alpha=0.25)
        ax.grid(axis="y", alpha=0.18)
    axs[1].set_xticks([1995, 2000, 2005, 2010, 2015, 2020, 2024])
    fig.tight_layout()
    _save_figure(fig, output_dir / "figure1.png", dpi=220, bbox_inches="tight")
    _save_figure(
        fig, output_dir.parent / "figures" / "figure1.pdf", bbox_inches="tight"
    )
    plt.close(fig)
    # Frisch-Waugh-Lovell partial relationship for baseline M3, for illustration.
    z = sample.dropna(subset=["g_house", "g_manufacturing", "g_gdp", "covid"])
    controls = np.column_stack([np.ones(len(z)), z.g_gdp, z.covid])

    def resid(v):
        return v - controls @ np.linalg.lstsq(controls, v, rcond=None)[0]

    rx, ry = resid(z.g_house.to_numpy()), resid(z.g_manufacturing.to_numpy())
    slope = float(results["M3"]["coefficients"]["g_house"]["beta"])
    assert abs(slope - float(rx @ ry / (rx @ rx))) < 1e-10
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    ax.scatter(rx, ry, c="#34495e", s=22)
    xx = np.array([min(rx) - 1, max(rx) + 1])
    ax.plot(xx, slope * xx, color="#111111", lw=1)
    for year in [2007, 2009, 2012, 2020, 2024]:
        ix = np.flatnonzero(z.year.to_numpy() == year)[0]
        ax.annotate(
            str(year),
            (rx[ix], ry[ix]),
            xytext=(3, 4),
            textcoords="offset points",
            fontsize=8,
        )
    ax.axhline(0, color="#bbbbbb", lw=0.5)
    ax.axvline(0, color="#bbbbbb", lw=0.5)
    ax.set_xlabel("House price growth after removing GDP growth and 2020 effect")
    ax.set_ylabel(
        "Manufacturing investment growth\nafter removing GDP growth and 2020 effect"
    )
    ax.grid(alpha=0.12)
    fig.tight_layout()
    _save_figure(fig, output_dir / "figure2.png", dpi=220, bbox_inches="tight")
    _save_figure(
        fig, output_dir.parent / "figures" / "figure2.pdf", bbox_inches="tight"
    )
    plt.close(fig)
