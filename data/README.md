# Data sources and preparation

This directory contains inputs for Estonian theatre activity in **2014–2025** and Business Register financial indicators in **2019–2025**. The main analytical unit is a production. The workbooks contain annual records or period totals, rather than individual performance records.

See the [project README](../README.md) for research questions, the reporting model, and dashboard measures.

## Files included

Paths below are relative to `data/`. All listed workbooks are present in the supplied project snapshot.

| Path | Contents | PostgreSQL import table |
|---|---|---|
| `raw/repertoire_yearly_2014_until_2025/teatrite_repertuaar_{year}.xlsx` | Twelve annual workbooks, 2014–2025 | `teater.repertuaar_kokku` |
| `raw/production_total_2014_until_2025/production_data_total_2014_until_2025.xlsx` | Combined production records and period totals | `teater.lavastused_koond` |
| `reference/production_name_correction.xlsx` | Production-title and premiere-date corrections | `teater.lavastuse_nimekorrektsioon` |
| `reference/business_registry_theaters.xlsx` | Theatre-to-legal-entity mapping | `teater.teater_ariuhing` |
| `processed/business_registry_financial_year_data_2019_until_2025/financial_year_data.xlsx` | Prepared annual-report line items | `teater.majandusaasta_andmed` |

`raw/` contains source workbooks supplied to the importer; `reference/` contains project matching and correction files; `processed/` contains financial data prepared before import. The main importer writes directly to PostgreSQL and does not generate these Excel files or intermediate CSVs.

## Sources and access

Acquisition dates are recorded in the project README, rather than inferred from workbook timestamps.

| Dataset | Provider / source | Coverage | Acquisition |
|---|---|---|---|
| Annual repertoire | Estonian Theatre Agency, [consolidated repertoire statistics](https://statistika.teater.ee/stat/stat_filter/show/repertoireConsolidatedList) | 2014–2025 | Downloaded 22 September 2026 |
| Combined production workbook | Estonian Theatre Agency, supplied by its head statistician by email | 2014–2025 | Received 23 September 2026 |
| Financial source downloads | Estonian Business Register, [open-data downloads](https://avaandmed.ariregister.rik.ee/et/avaandmete-allalaadimine) | Report years 2019–2025 | Downloaded 21 September 2026 |
| Correction and theatre mapping files | Project reference files | Cross-source matching | Preparation dates and review history are not recorded |

To obtain new repertoire exports, select each reporting year and the required theatre scope on the Agency portal and use its XLS export. The repository contains `.xlsx` files; the conversion from downloaded exports is not documented. Prepare genuine `.xlsx` workbooks with the structure below: changing the filename extension alone does not convert a workbook. Later downloads may include revisions, so use the supplied snapshot to reproduce the original project results.

The combined production workbook includes some information that is not publicly available. It cannot be recreated from annual public repertoire downloads alone. Obtain an authorised copy from the Agency if it is not supplied with your copy of the project.

**Access and redistribution:** inclusion in this snapshot does not establish permission to redistribute source data. Confirm the Agency's permission for the supplied workbook and any derived data included in the Power BI report. Follow the Business Register's source terms. The repository's MIT licence for the team's work does not establish licensing terms for third-party datasets.

## Workbook structure and fields

The importer reads the **first worksheet only**. Keep the intended worksheet first; additional worksheets are ignored. Retain source spelling where the SQL expects it, including apparent spelling errors.

### Annual repertoire

Headings are on **Excel row 3**. Ownership labels appear in section rows with only `TEATER` populated. Python carries each label forward to the following records and removes the section rows.

| Excel heading | Imported column | Meaning |
|---|---|---|
| `TEATER` | `teater` | Reporting theatre |
| `Autor / dramatiseerija` | `autor` | Author or adapter |
| `Autor või teksti päritolumaa` | `autor_paev_paritolumaa` | Author's or text's country of origin; imported name retained for compatibility |
| `Teksti tüüp` | `teksti_tyyp` | Text type |
| `Lavastuse pealkiri` | `lavastuse_pealkiri` | Production title |
| `Lavastuse liik` | `lavastuse_liik` | Production type |
| `Žanr` | `zanr` | Genre |
| `Esietendus` | `esietendus` | Premiere date, parsed later in SQL |
| `Sihtgrupp` | `sihtgrupp` | Target audience |
| `Statsionaar` | `statsionaar` | Reported venue / hall label |
| `Esituskorrad kokku` | `esituskorrad_kokku` | Performances in the reporting year |
| `Piletitulu` | `piletitulu` | Reported ticket revenue |
| `Külastajaid kokku` (2014–2019), `Külastajaid` (2020–2025) | `kylastajaid_kohapeal` | Onsite attendance |
| `VEEBIKÜLASTAJAID` (2020–2025) | `veebis_kylastajaid` | Online attendance |
| Derived from section rows | `omandivorm` | Ownership classification |
| Derived from the configured file year | `andmeaasta` | Reporting year |

Online attendance is absent in 2014–2019 and remains missing; Python does not replace it with zero. The loader normalizes heading capitalization and whitespace, rejects unknown headings and duplicate mapped columns, and checks required fields.

### Combined production data

The first worksheet is `2014-25`, with headings on **row 1** and **3,186 records**. Metrics cover the full 2014–2025 period. There is no reporting-year column; a row is not necessarily a unique production across all theatres and halls.

| Field group | Excel headings | Purpose |
|---|---|---|
| Theatre and ownership | `TEATER`, `Omanik` | Reporting theatre and ownership |
| Description | `Autor / dramatiseerija`, `Autor või teksti päritolumaa`, `Teksti tüüp`, `Lavastuse pealkiri`, `Lavastuse liik`, `Žanr`, `Esietendus`, `Uuslavastus`, `Sihtgrupp` | Production attributes and source status |
| Hall and troupe | `Statsionaarne saal`, `Istekohtade arv`, `Trupi liikmete arv` | Reported hall, seats, and troupe size |
| Activity | `Esituskorrad kokku`, `Kohapealseid külastajaid`, `Külastajais veebis`, `Müüdud piletid`, `Piletitulu` | Period totals |
| Touring and cooperation | `Külalisetendused`, `Maakonnade arv`, `Välismaal antud etendused`, `Koostöölavastus` | Touring indicators and co-production flag |

Python normalizes headings and production titles, while preserving Excel-inferred numeric and date types. For example, `Müüdud piletid` becomes `myydud_piletid`. Premiere dates in the supplied file use `DD.MM.YYYY` text. SQL interprets `Koostöölavastus = jah` as cooperation.

### Production corrections

The first worksheet is `lavastuse_nimekorrektsioon`, with headings on **row 1** and **four records**.

| Column | Use |
|---|---|
| `lavastuse_pealkiri_algne` | Original title to match |
| `esietendus` | Original premiere date to match |
| `autor_dramatiseerija` | Author text to match |
| `lavastuse_pealkiri_parandatud` | Replacement title |
| `esietendus_parandatud` | Replacement premiere date |
| `id` | Correction reference identifier |

SQL matches original title, date, and author against the imported repertoire table, then updates its title and date. It does not update the combined production workbook. Python trims text in the correction file but does not apply title normalization there. New correction keys must match the **Python-cleaned repertoire values**.

Against this snapshot, correction IDs 1–4 match 2, 7, 3, and 1 repertoire records respectively before SQL updates. A correction may match multiple reporting years.

### Theatre-to-business mapping

The first worksheet contains **84 records**, with headings on **row 1**.

| Column | Use |
|---|---|
| `teater` | Theatre name used to connect financial and theatre reporting |
| `arinimi` | Legal entity name |
| `ariregistri_kood` | Registry code used for the financial join |
| `lukustatud` | Reference flag; meaning undocumented and not used by the current SQL |

One legal entity can map to multiple theatre names. Registry code `80363768` maps to both `Arena` and `Improteater Impeerium`. The financial view attributes that entity's figures to each mapped theatre. Confirm the intended treatment before summing financial totals across these theatres.

### Prepared financial data

The first worksheet is `andmed`, with headings on **row 1** and **7,264 records** covering **74 registry codes** and years **2019–2025**.

| Excel column | Imported column | Meaning |
|---|---|---|
| `ariregistri_kood` | `ariregistri_kood` | Legal entity identifier |
| `nimi` | `nimi` | Entity name in the financial source |
| `aruandeaasta` | `aruandeaasta` | Financial report year |
| `aruanne` | `aruanne` | Statement or note type |
| `rida` | `rida` | Line-item label |
| `väärtus` | `vaartus` | Reported numerical value |

This snapshot has no duplicate combinations of registry code, year, statement, and line item. All its registry codes occur in the mapping. These checks are not enforced by the importer.

The reporting SQL selects items from `Tulemiaruanne`, `Kasumiaruanne skeem 1`, `Bilanss`, and `Lisa: Tööjõukulud`, aggregates mapped entities, and pivots values into reporting columns. Other statement types remain in the source table. Preserve original value signs: SQL applies its own sign adjustments.

## Financial-data preparation

The [filtering notebook](../scripts/business_registry_filtering.ipynb) uses DuckDB to select companies by name pattern or registry code, select annual reports for 2019–2025, and join report elements. Its configured registry-code list covers all 74 registry codes in the supplied financial workbook. The bulk CSV downloads are **not included**.

Its configured paths are relative to the notebook's working directory:

| Input | Purpose |
|---|---|
| `baasandmed/ettevotja_rekvisiidid__lihtandmed.csv` | Entity names and registry codes |
| `baasandmed/1.aruannete_yldandmed_kuni_31082026.csv` | Annual-report metadata |
| `baasandmed/2.EMTAK_myygitulu_kuni_31082026.csv` | Activity-classification revenue data |
| `baasandmed/4.{year}_aruannete_elemendid.csv`, 2019–2025 | Annual-report elements |

Obtain the corresponding Business Register downloads and update the notebook's paths. These dated filenames describe the configured snapshot, not guaranteed names for future downloads. The annual-report CSV queries explicitly use semicolon delimiters.

The notebook uses `duckdb`, `pandas`, and `openpyxl`, which are included in `requirements.txt`. Run it in a Jupyter-compatible environment; Jupyter itself is not included in the dependency file.

It writes the following outputs in its working directory:

| Output | Format and use |
|---|---|
| `financial_year_data.xlsx` | Financial line items on the `andmed` worksheet, with column headings and no DataFrame index; input to the main importer |
| `financial_year_data.csv` | The same financial extraction as a semicolon-separated CSV, encoded as UTF-8 with a byte-order mark |
| `emtak_data` | EMTAK revenue extraction as a semicolon-separated CSV, encoded as UTF-8 with a byte-order mark; the reviewed notebook saves this file without an extension |

For a `.csv` extension on the EMTAK output, use `salvesta_nimega_emtak + ".csv"` in its `to_csv` call. The main importer reads neither CSV, and the supplied reporting SQL does not use the EMTAK output.

After running the notebook, place `financial_year_data.xlsx` in `data/processed/business_registry_financial_year_data_2019_until_2025/` before running the main importer. The notebook does not move the workbook there automatically.

**Reproduction status:** Excel generation is now implemented, and the configured registry-code list covers the entities in the supplied workbook. Exact regeneration of the supplied snapshot has not been verified because the bulk source CSVs are not included. Preserve the source-download versions and document the treatment of revised reports and any manual adjustments. Compare the regenerated workbook with the supplied snapshot before replacing it.

## Import and reporting

Run from the repository root.

```bash
python -m pip install -r requirements.txt
python scripts/raw_data_cleaning_loading.py --dry-run
```

The script requires Python 3.10+ and derives the repository root from its location directly inside `scripts/`. The dry run reads all five datasets without connecting to PostgreSQL. It checks the implemented import rules, rather than validating the later SQL or Power BI refresh.

Create the PostgreSQL database and configure these environment variables as needed:

| Variable | Default / behaviour |
|---|---|
| `PGHOST` | `localhost` |
| `PGPORT` | `5432` |
| `PGDATABASE` | `postgres` |
| `PGUSER` | `postgres` |
| `PGPASSWORD` | If absent, password is requested securely |

The schema is configured as `teater`. Set variables in the process environment; the script does not automatically load `.env` files. After validation succeeds and the database connection is configured, run the import:

```bash
python scripts/raw_data_cleaning_loading.py
```

The import replaces all five tables in one transaction. Replacement recreates their definitions and can be blocked by dependent views. Next, execute [the SQL script](../sql/view_creation_postgres.txt), then configure and refresh [the Power BI report](../powerbi/theater_agency_analysis.pbix).

SQL applies corrections, changes repertoire hall columns, and creates **seven views**: `dim_lavastused`, `dim_teater`, `dim_saal`, `dim_aeg`, `fact_repertuaar`, `fact_moodikud`, and `fact_majandusaasta`.

**Reruns:** the SQL expects newly imported tables in a fresh reporting schema. It cannot be rerun unchanged because it renames `statsionaar` to `statsionaar_algandmed`, which already exists after the first run. The views, including `fact_majandusaasta`, use `CREATE OR REPLACE VIEW`; view creation is not the cause of this rename failure. Test in a disposable database. Establish a migration or rebuild procedure before refreshing an existing reporting database.

## Expected snapshot counts

The full import dry run passed for these files. Counts below are after Python cleaning and before SQL aggregation.

| Dataset | Rows |
|---|---:|
| Repertoire 2014 | 525 |
| Repertoire 2015 | 568 |
| Repertoire 2016 | 548 |
| Repertoire 2017 | 571 |
| Repertoire 2018 | 596 |
| Repertoire 2019 | 617 |
| Repertoire 2020 | 554 |
| Repertoire 2021 | 587 |
| Repertoire 2022 | 673 |
| Repertoire 2023 | 734 |
| Repertoire 2024 | 739 |
| Repertoire 2025 | 718 |
| **Combined repertoire** | **7,430** |
| Combined production data | 3,186 |
| Corrections | 4 |
| Theatre mappings | 84 |
| Financial data | 7,264 |

Import counts differ from unique-production counts and final-view row counts. PostgreSQL execution and Power BI refresh need separate verification.

## Cleaning and interpretation

- Text cleaning uses Unicode NFC normalization, trims surrounding whitespace, treats empty strings as missing, and removes completely empty rows.
- Title cleaning standardizes quotation marks and repeated whitespace in repertoire and production data. It does not establish production identity by itself.
- Repertoire numbers are converted after removing whitespace and replacing decimal commas with decimal points. Unexpected text causes an error. Other loaders preserve Excel-inferred types.
- SQL parses premiere dates. All dates in the supplied repertoire and combined production data were valid `DD.MM.YYYY` values in the snapshot check.
- Production identity in SQL is title plus premiere date across theatres. Separate productions sharing these values can merge. Generated production IDs can shift when inputs change.
- Co-production records retain theatre-specific values. Historical reporting differences, especially in 2014–2019, affect comparisons; matching titles alone do not justify deduplication.
- Period-total ticket sales have no year key. Match time coverage when comparing them with annual attendance or revenue; year filters do not directly filter `fact_moodikud`.
- Hall labels and seating figures are not a verified physical-venue register. Consolidated locations cannot establish where each performance occurred.
- There are 16 repertoire records with zero performances. SQL derives the last reported year from all repertoire rows without requiring positive performance counts. Interpret lifespan and 2025 status using that implemented rule.
- Financial values follow the reference mapping, and SQL sometimes substitutes zero for missing items. Inspect coverage before interpreting zero as an observed result.

## Details still to confirm

Before final publication, record the Agency's redistribution permission and source-data terms, the reference files' preparation and review history (including `lukustatud`), and full financial-workbook preparation steps. Confirm reporting currency and units from the original exports: the included files do not provide a complete unit definition. Keep source-data terms separate from the licence for the team's code and documentation.
