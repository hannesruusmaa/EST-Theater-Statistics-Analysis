"""Clean annual repertuaar Excel files and the combined lavastused workbook.

MIDA TEHA:
- jooksuta terminalis install command 'python -m pip install pandas openpyxl sqlalchemy psycopg2-binary'
- paranda repertuaar ja lavastuse PATH ära vastavalt enda arvutile (Read 41 ja 45)
- jooksuta 'python "MAIN_teatri_excel_import.py"' kood terminalis
    - kui see ei tööta, siis vaata, et terminal oleks õiges kaustas, seda saab parandada 'cd "ÕIGE KAUSTA PATH"'
- ta küsib terminalis parooli 'andmed' kirjuta see terminali sisse
    - NB! sa ei näe tähti, kui sa kirjutad. Ehk kirjuta parool ära ja vajuta enter. 
- palju õnne, sul on postgres'is andmed.

Python 3.10+. Install once:
    python -m pip install pandas openpyxl sqlalchemy psycopg2-binary

Edit the paths below, then run:
    python MAIN_teatri_excel_import.py --dry-run
    python MAIN_teatri_excel_import.py

    
The first sheet is read from each workbook. Repertuaar headings are on row 3;
lavastused headings are on row 1. All configured years must be present.

Writes teatriliit.repertuaar_kokku and teatriliit.lavastused_koond directly;
no intermediate CSV. Both tables are REPLACED, as in the original importers.
Replacement recreates tables: custom indexes/constraints/grants are not retained.
Both replacements use one PostgreSQL transaction; a failure rolls both back.
Rows are not deduplicated: a shared title alone does not identify a production.
Existing views referencing these tables may prevent replacement (no CASCADE).
"""

import argparse
import getpass
import os
import re
import unicodedata
from pathlib import Path

import pandas as pd

# ---------- Configuration: edit these paths to match your computer ----------
# The uploaded scripts used two different repository roots; verify both paths.
REPERTUAAR_DIR = Path(
     r"C:\Users\opilane\Documents\GitHub\teatriliit"
    #or
    #r"C:\Users\Administrator\Documents\GitHub\teatriliit"
    #and
    r"\Baasandmed\statistika_teater_ee\repertuaar\puhastamata"
)
LAVASTUSED_FILE = Path(
     r"C:\Users\opilane\Documents\GitHub\teatriliit"
    #or
    #r"C:\Users\Administrator\Documents\GitHub\teatriliit"
    #and
    r"\Baasandmed\statistika_teater_ee\lavastused\puhastamata"
    r"\2014-2025LAVastused.xlsx"
)
LAVASTUSE_NIMEKORREKTSIOON_FILE = Path(
     r"C:\Users\opilane\Documents\GitHub\teatriliit"
    #or
    #r"C:\Users\Administrator\Documents\GitHub\teatriliit"
    #and
    r"\Baasandmed\statistika_teater_ee\repertuaar\puhastamata"
    r"\lavastuse_nimekorrektsioon.xlsx"
)

TEATER_ARIUHING_FILE = Path(
     r"C:\Users\opilane\Documents\GitHub\teatriliit"
    #or
    #r"C:\Users\Administrator\Documents\GitHub\teatriliit"
    #and
    r"\Baasandmed\ariregister"
    r"\teater_ariuhingud.xlsx"
)

MAJANDUSAASTA_ANDMED_FILE = Path(
     r"C:\Users\opilane\Documents\GitHub\teatriliit"
    #or
    #r"C:\Users\Administrator\Documents\GitHub\teatriliit"
    #and
    r"\Baasandmed\ariregister"
    r"\majandusaasta_andmed.xlsx"
)

FILE_PATTERN = "teatrite_repertuaar_{year}.xlsx"
START_YEAR, END_YEAR = 2014, 2025
SCHEMA = "teatriliit"
DB_HOST = os.environ.get("PGHOST", "localhost")
DB_PORT = int(os.environ.get("PGPORT", "5432"))
DB_NAME = os.environ.get("PGDATABASE", "postgres")
DB_USER = os.environ.get("PGUSER", "postgres")
# Password is read from PGPASSWORD or requested securely at runtime.

# Only these title columns are normalized; headings otherwise stay compatible.
# Add your actual normalized heading here if it differs.
TITLE_COLUMNS = {
    "lavastuse_pealkiri", "lavastuse_nimi", "lavastuse_nimetus",
    "etenduse_nimi", "etenduse_nime", "etenduse_pealkiri",
}


def clean_text(df):
    """Trim text, standardize Unicode, preserve missing values and numbers."""
    def clean(value):
        if isinstance(value, str):
            value = unicodedata.normalize("NFC", value).strip()
            return value if value else pd.NA
        return value

    for column in df.columns:
        df[column] = df[column].map(clean)
    return df.dropna(how="all")


def normalize_title(value):
    if not isinstance(value, str):
        return value

    value = unicodedata.normalize("NFC", value)

    # Convert common quotation marks to a straight apostrophe.
    value = value.translate(str.maketrans({
        char: "'" for char in "\"´`“”„‟‘’‚‛«»‹›"
    }))

    # Treat repeated quotation marks as one.
    value = re.sub(r"'{2,}", "'", value)

    return " ".join(value.split()) or pd.NA


def clean_titles(df, label, candidates=None):
    columns = sorted(set(df.columns) & (TITLE_COLUMNS if candidates is None else candidates))
    if not columns:
        raise ValueError(
            f"{label}: no recognized title column. Found: {list(df.columns)}. "
            "Add the correct heading to TITLE_COLUMNS."
        )
    for column in columns:
        before = df[column].copy()
        df[column] = df[column].map(normalize_title)
        changed = (before.fillna("") != df[column].fillna("")).sum()
        print(f"{label}: normalized {changed:,} titles in {column}")
    return df


def clean_column_names(df):
    translation = str.maketrans({
        'õ': 'o', 'ä': 'a', 'ö': 'o', 'ü': 'y', 'ž': 'z', ' ': '_', '/': '_'
    })
    df.columns = [
        re.sub(r'_+', '_', " ".join(unicodedata.normalize("NFC", str(c)).split())
               .lower().translate(translation)) for c in df.columns
    ]
    if df.columns.duplicated().any():
        raise ValueError("Duplicate column headings after normalization.")
    # PostgreSQL truncates identifiers beyond 63 bytes; fail before writing.
    if any(len(c.encode("utf-8")) > 63 for c in df.columns):
        raise ValueError("A column heading exceeds PostgreSQL's 63-byte limit.")
    return df


COLUMN_MAPPING = {
    "teater": "teater",
    "autor / dramatiseerija": "autor",
    "autor või teksti päritolumaa": "autor_paev_paritolumaa",
    "teksti tüüp": "teksti_tyyp",
    "lavastuse pealkiri": "lavastuse_pealkiri",
    "lavastuse liik": "lavastuse_liik",
    "žanr": "zanr",
    "esietendus": "esietendus",
    "sihtgrupp": "sihtgrupp",
    "statsionaar": "statsionaar",
    "esituskorrad kokku": "esituskorrad_kokku",
    "piletitulu": "piletitulu",
    "külastajaid kokku": "kylastajaid_kohapeal",
    "külastajaid": "kylastajaid_kohapeal",
    "veebikülastajaid": "veebis_kylastajaid",
}

OUTPUT_COLUMNS = [
    "omandivorm",
    "teater",
    "autor",
    "autor_paev_paritolumaa",
    "teksti_tyyp",
    "lavastuse_pealkiri",
    "lavastuse_liik",
    "zanr",
    "esietendus",
    "sihtgrupp",
    "statsionaar",
    "esituskorrad_kokku",
    "piletitulu",
    "kylastajaid_kohapeal",
    "veebis_kylastajaid",
    "andmeaasta",
]

NUMERIC_COLUMNS = [
    "esituskorrad_kokku",
    "piletitulu",
    "kylastajaid_kohapeal",
    "veebis_kylastajaid",
]


def load_year(path, year):

    # The third Excel row contains the column headings.
    df = pd.read_excel(path, header=2).dropna(how="all")

    # Normalize heading capitalization and extra spaces.
    df.columns = [
        " ".join(str(column).split()).casefold()
        for column in df.columns
    ]

    unknown = set(df.columns) - set(COLUMN_MAPPING)

    if unknown:
        raise ValueError(
            f"{path.name}: unrecognized headings: {sorted(unknown)}"
        )

    df = df.rename(columns=COLUMN_MAPPING)

    if df.columns.duplicated().any():
        raise ValueError(
            f"{path.name}: duplicate columns after renaming."
        )

    required = set(OUTPUT_COLUMNS) - {
        "omandivorm",
        "andmeaasta",
        "veebis_kylastajaid",
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"{path.name}: missing columns: {sorted(missing)}"
        )

    # Older files do not contain web visitor numbers.
    if "veebis_kylastajaid" not in df.columns:
        df["veebis_kylastajaid"] = pd.NA

    df = clean_text(df)

    # Ownership labels appear in separate rows under TEATER.
    # These rows have no values in the other columns.
    section_rows = (
        df["teater"].notna()
        & df.drop(columns="teater").isna().all(axis=1)
    )

    # Apply each ownership label to the following data rows.
    df["omandivorm"] = (
        df["teater"]
        .where(section_rows)
        .astype("string")
        .str.strip()
        .ffill()
    )

    # Remove the ownership section rows themselves.
    df = df.loc[~section_rows].copy()

    # Convert numeric fields, handling decimal commas and spaces.
    for column in NUMERIC_COLUMNS:
        if column not in df.columns:
            continue

        cleaned = (
            df[column]
            .astype("string")
            .str.replace(r"\s+", "", regex=True)
            .str.replace(",", ".", regex=False)
            .replace("", pd.NA)
        )

        numbers = pd.to_numeric(cleaned, errors="coerce")

        # Stop if unexpected text would otherwise be lost.
        invalid = cleaned.notna() & numbers.isna()

        if invalid.any():
            examples = df.loc[invalid, column].head(5).tolist()
            raise ValueError(
                f"{path.name}: invalid values in "
                f"'{column}': {examples}"
            )

        df[column] = numbers

    # Preserve the year each record came from.
    df["andmeaasta"] = year

    df = clean_titles(df, path.name, {"lavastuse_pealkiri"})

    # Use the same column order for every year.
    df = df[OUTPUT_COLUMNS]

    print(f"{year}: loaded {len(df):,} rows")
    return df


def load_lavastused(path):
    # Preserve all columns and Excel-inferred numeric/date types. The original
    # lavastused importer did not specify numeric conversions or row filtering.
    df = pd.read_excel(path, header=0).dropna(how="all")
    df = clean_text(clean_column_names(df))
    df = clean_titles(df, path.name)
    if df.empty:
        raise ValueError(f"{path.name}: no production data found.")
    print(f"Lavastused: loaded {len(df):,} rows")
    return df

def load_nimekorrektsioon(path):
    # Preserve all columns and Excel-inferred numeric/date types. The original
    # lavastused importer did not specify numeric conversions or row filtering.
    df = pd.read_excel(path, header=0).dropna(how="all")
    df = clean_text(clean_column_names(df))
    #df = clean_titles(df, path.name)
    if df.empty:
        raise ValueError(f"{path.name}: no production data found.")
    print(f"Nimekorrektsioon: loaded {len(df):,} rows")
    return df

def load_teater_ariuhingud(path):
    # Preserve all columns and Excel-inferred numeric/date types. The original
    # lavastused importer did not specify numeric conversions or row filtering.
    df = pd.read_excel(path, header=0).dropna(how="all")
    df = clean_text(clean_column_names(df))
    #df = clean_titles(df, path.name)
    if df.empty:
        raise ValueError(f"{path.name}: no production data found.")
    print(f"teater-ariuhingud: loaded {len(df):,} rows")
    return df


def load_majandusaasta_andmed(path):
    # Preserve all columns and Excel-inferred numeric/date types. The original
    # lavastused importer did not specify numeric conversions or row filtering.
    df = pd.read_excel(path, header=0).dropna(how="all")
    df = clean_text(clean_column_names(df))
    #df = clean_titles(df, path.name)
    if df.empty:
        raise ValueError(f"{path.name}: no production data found.")
    print(f"majandusaasta andmed: loaded {len(df):,} rows")
    return df

def write_database(repertuaar, lavastused, lavastuse_nimekorrektsioon, teater_ariuhing, majandusaasta_andmed):
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import URL
    from sqlalchemy.types import TEXT

    password = os.environ.get("PGPASSWORD")
    if password is None:
        password = getpass.getpass(f"PostgreSQL password for {DB_USER}: ")
    url = URL.create("postgresql+psycopg2", username=DB_USER,
                     password=password, host=DB_HOST, port=DB_PORT, database=DB_NAME)
    engine = create_engine(url, hide_parameters=True)
    try:
        with engine.begin() as connection:
            # Quote the schema name instead of interpolating an SQL identifier.
            schema_sql = connection.dialect.identifier_preparer.quote_identifier(SCHEMA)
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_sql}"))
            for name, df in [("repertuaar_kokku", repertuaar),
                             ("lavastused_koond", lavastused),
                             ("lavastuse_nimekorrektsioon", lavastuse_nimekorrektsioon),
                             ("teater_ariuhing", teater_ariuhing),
                             ("majandusaasta_andmed", majandusaasta_andmed)]:
                text_types = {column: TEXT() for column in df.columns
                              if pd.api.types.is_object_dtype(df[column].dtype)
                              or isinstance(df[column].dtype, pd.StringDtype)}
                df.to_sql(name, con=connection, schema=SCHEMA,
                          if_exists="replace", index=False,
                          dtype=text_types, chunksize=1000)
                print(f"Prepared {SCHEMA}.{name}: {len(df):,} rows")
        print("Success: both tables committed to PostgreSQL.")
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repertuaar-dir", type=Path, default=REPERTUAAR_DIR)
    parser.add_argument("--lavastused-file", type=Path, default=LAVASTUSED_FILE)
    parser.add_argument("--lavastuse_nimekorrektsioon-file", type=Path, default=LAVASTUSE_NIMEKORREKTSIOON_FILE)
    parser.add_argument("--teater_ariuhing-file", type=Path, default=TEATER_ARIUHING_FILE)
    parser.add_argument("--majandusaasta_andmed-file", type=Path, default=MAJANDUSAASTA_ANDMED_FILE)
    parser.add_argument("--start-year", type=int, default=START_YEAR)
    parser.add_argument("--end-year", type=int, default=END_YEAR)
    parser.add_argument("--dry-run", action="store_true",
                        help="Read and validate everything without connecting to PostgreSQL.")
    args = parser.parse_args()
    if args.start_year > args.end_year:
        parser.error("--start-year must not exceed --end-year")
    years = range(args.start_year, args.end_year + 1)
    paths = [(year, args.repertuaar_dir / FILE_PATTERN.format(year=year)) for year in years]
    missing = [str(path) for path in [*(p for _, p in paths), args.lavastused_file]
               if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing input files:\n" + "\n".join(missing))
    repertuaar = pd.concat([load_year(path, year) for year, path in paths], ignore_index=True)
    if repertuaar.empty:
        raise ValueError("Repertuaar files contain no data.")
    lavastused = load_lavastused(args.lavastused_file)
    lavastuse_nimekorrektsioon = load_nimekorrektsioon(args.lavastuse_nimekorrektsioon_file)
    teater_ariuhing = load_teater_ariuhingud(args.teater_ariuhing_file)
    majandusaaseta_andmed = load_majandusaasta_andmed(args.majandusaasta_andmed_file)
    print(f"Validated: {len(repertuaar):,} repertuaar rows, {len(lavastused):,} lavastused rows., {len(lavastuse_nimekorrektsioon):,} nimekorrektsiooni rows.")

    
    if args.dry_run:
        print("Dry run complete. No database connection or changes made.")
        return
    write_database(repertuaar, lavastused, lavastuse_nimekorrektsioon, teater_ariuhing, majandusaaseta_andmed)


if __name__ == "__main__":
    main()
