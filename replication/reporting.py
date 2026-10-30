"""Export analysis results and the empirical LaTeX table rows used by the paper."""

from pathlib import Path
import json
import pandas as pd


def write_results(data, results, output_dir: Path):
    """Write the annual dataset, complete results, and tidy CSV summaries."""
    output_dir.mkdir(parents=True, exist_ok=True)
    data.to_csv(output_dir / "analysis_data.csv", index=False, float_format="%.10f")
    (output_dir / "results.json").write_text(json.dumps(results, indent=2))
    rows = []
    for model, result in results["models"].items():
        for term, values in result["coefficients"].items():
            rows.append(
                dict(
                    model=model,
                    term=term,
                    n=result["n"],
                    r2=result["r2"],
                    hac_lags=result["hac_lags"],
                    **values,
                )
            )
    pd.DataFrame(rows).to_csv(output_dir / "regression_results.csv", index=False)
    pd.DataFrame(results["summary"]).T.to_csv(output_dir / "summary_statistics.csv")


def _number(value, places=3):
    return f"${value:.{places}f}$"


def _row(label, values):
    return " & ".join([label, *values]) + r"\\" + "\n"


def write_tables(results, diagnostics, table_dir: Path):
    """Render Tables 2, 3, 4, and 6 directly from saved numerical results.

    Captions, labels, and source notes remain in main.tex. Column layouts
    are editable templates in replication/table_layouts/.
    Source definitions (Table 1) and literature estimates (Table 5) are static.
    """
    table_dir.mkdir(parents=True, exist_ok=True)
    models = results["models"]
    summary_rows = []
    variables = [
        ("Manufacturing investment", "g_manufacturing"),
        ("Real house prices", "g_house"),
        ("Real GDP", "g_gdp"),
        ("Manufacturing equipment", "g_equipment"),
        ("Manufacturing intellectual property", "g_ipp"),
    ]
    for label, variable in variables:
        values = results["summary"][variable]
        summary_rows.append(
            _row(
                label,
                [
                    f"${values['n']}$",
                    *[
                        _number(values[key], 2)
                        for key in ("mean", "sd", "minimum", "maximum")
                    ],
                ],
            )
        )

    main_rows = []
    model_names = ("M1", "M2", "M3", "M4")
    for label, term in [
        ("House price growth", "g_house"),
        ("GDP growth", "g_gdp"),
        ("2020 indicator", "covid"),
        ("Lagged house price growth", "lag_house"),
        ("Constant", "constant"),
    ]:
        cells = []
        for name in model_names:
            coefficient = models[name]["coefficients"].get(term)
            if coefficient is None:
                cells.append(r"\textemdash")
            else:
                cells.append(
                    r"\shortstack{"
                    + _number(coefficient["beta"])
                    + r"\\"
                    + f"$({coefficient['se']:.3f})$"
                    + "}"
                )
        main_rows.append(_row(label, cells))
    main_rows.append(_row("Observations", [f"${models[m]['n']}$" for m in model_names]))
    main_rows.append(_row(r"$R^2$", [_number(models[m]["r2"]) for m in model_names]))
    main_rows.append(
        _row(
            "House coefficient p-value",
            [_number(models[m]["coefficients"]["g_house"]["p"]) for m in model_names],
        )
    )

    sensitivity_rows = []
    for label, model in [
        ("Equipment investment", "R1_equipment"),
        ("Intellectual property investment", "R2_ipp"),
        ("1996--2007 sample", "R3_pre2008"),
        ("1996--2007 excluding 2000", "R8_pre2008_omit2000"),
        ("2001--2007 sample", "R9_boom_only"),
        ("Exclude 2020 and 2021", "R4_exclude_covid"),
        ("HAC with two annual lags", "R5_hac2"),
        ("Add lagged investment growth", "R6_AR1"),
        ("End sample in 2023", "R7_to2023"),
    ]:
        result = models[model]
        coefficient = result["coefficients"]["g_house"]
        sensitivity_rows.append(
            _row(
                label,
                [
                    f"${result['n']}$",
                    _number(coefficient["beta"]),
                    f"$[{coefficient['lo']:.3f}, {coefficient['hi']:.3f}]$",
                    _number(coefficient["p"]),
                ],
            )
        )

    diagnostic_rows = []
    for label, variable in [
        ("Manufacturing investment", "g_manufacturing"),
        ("Real house price", "g_house"),
        ("Real GDP", "g_gdp"),
    ]:
        result = diagnostics[variable + "_ADF"]
        diagnostic_rows.append(
            _row(
                label + " growth",
                [
                    f"${result['n']}$",
                    _number(result["statistic"]),
                    _number(result["p"]),
                ],
            )
        )

    files = {
        "descriptive_table.tex": summary_rows,
        "main_models_table.tex": main_rows,
        "sensitivity_table.tex": sensitivity_rows,
        "diagnostics_table.tex": diagnostic_rows,
    }
    for filename, rows in files.items():
        template = (Path(__file__).parent / "table_layouts" / filename).read_text()
        if template.count("%%ROWS%%") != 1:
            raise ValueError(
                f"Table layout {filename} must have exactly one row marker"
            )
        (table_dir / filename).write_text(
            "% Generated by replication/render_tables.py; edit the code or layout template.\n"
            + template.replace("%%ROWS%%", "".join(rows).rstrip())
        )
    return tuple(table_dir / filename for filename in files)
