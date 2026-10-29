# Data sources and transformations

The archived public-source responses were retrieved on **29 October 2026**. Exact query URLs, filters, software versions, and SHA-256 hashes are recorded in [`source_manifest.json`](source_manifest.json). The scripts read local snapshots and do not fetch live data.

| Raw file | Provider and dataset | Selection used |
| --- | --- | --- |
| `manufacturing_raw.json` | [Eurostat `nama_10_a64_p5`](https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10_a64_p5?geo=ES&nace_r2=C&na_item=P51G&sinceTimePeriod=1995&untilTimePeriod=2024) | Spain; annual; manufacturing `C`; gross fixed capital formation `P51G`; assets `N11G`, `N11MG`, `N117G`; unit `CLV20_MEUR` |
| `gdp_raw.json` | [Eurostat `nama_10_gdp`](https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10_gdp?geo=ES&na_item=B1GQ&sinceTimePeriod=1995&untilTimePeriod=2024) | Spain; annual; GDP `B1GQ`; unit `CLV20_MEUR` |
| `investment_raw.json` | [Eurostat `nama_10_an6`](https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10_an6?geo=ES&sinceTimePeriod=1995&untilTimePeriod=2024) | Spain; annual; dwellings `N111G`; unit `CLV20_MEUR`; retained for completeness |
| `house_raw.csv` | [FRED `QESR628BIS`](https://fred.stlouisfed.org/series/QESR628BIS), from the [BIS Residential Property Price database](https://www.bis.org/statistics/pp.htm) and national sources | Quarterly real residential property price index for Spain; annual arithmetic mean of four quarters |

`CLV20_MEUR` denotes chain-linked volumes in millions of euros with reference year 2020. Annual levels cover 1995–2024. Raw responses may contain additional categories or periods; only the script selections are used.

## Derived dataset columns

| Columns | Meaning |
| --- | --- |
| `year` | Calendar year |
| `manufacturing` | Total manufacturing gross fixed capital formation |
| `equipment` | Manufacturing machinery and equipment investment |
| `ipp` | Manufacturing intellectual property products investment |
| `gdp` | Real GDP |
| `dwelling` | Dwelling investment; excluded from reported regressions |
| `house` | Annual mean of four quarterly real house-price observations |
| `g_manufacturing`, `g_equipment`, `g_ipp`, `g_gdp`, `g_dwelling`, `g_house` | Annual log changes multiplied by 100 |
| `lag_house`, `lag_manufacturing` | Previous year's corresponding growth rate |
| `covid` | Indicator equal to one for 2020 |

Growth is missing in 1995 by construction; lagged growth first becomes available in 1997. The scripts do not interpolate or simulate observations. Source status flags are retained in `results.json` under `status`; consult those flags before interpreting recent observations as final.

## Integrity, revisions, and attribution

`python reproduce.py` validates all four raw-file hashes before rebuilding outputs. Fresh downloads may contain revisions and represent a new analysis rather than an exact reproduction. Do not silently replace raw files or change hashes to make unexpected inputs pass.

Attribution: **Eurostat national accounts; national sources and the BIS Residential Property Price database, retrieved via FRED series QESR628BIS.** The MIT software license does not apply to these third-party observations. Check the providers' current reuse terms when redistributing or using data in another product.
