# Estonian Theatre Data Analysis, 2014–2025

An analysis of Estonian theatre productions, their lifespan, and performance activity using Python, PostgreSQL, and Power BI.

Developed as a group final project for the BCS data analysis microprogram.

> **Status:** Work in progress. Analysis, documentation, and final deliverables are being completed.


## Project overview

This project examines how long Estonian theatre productions remain in the repertoire and how their lifespan relates to performances, attendance, and ticket sales during 2014–2025. It brings together production, repertoire, and theatre statistics to support analysis relevant to the Estonian Theatre Agency.

The main unit of analysis is a **production**, rather than an individual performance:

- **Production:** The artistic work staged by a theatre or collaborating theatres.
- **Performance:** A single staging of a production.
- **Attendance:** Audience visits, including both paid tickets and invitations; not necessarily unique people.
- **Tickets sold:** Paid tickets, distinguished from total attendance.

## Research questions

- How long do productions remain in the repertoire?
- How does production lifespan vary by production type, theatre, and ownership form?
- How is lifespan related to the number of performances and audience visits?
- How do tickets sold compare with total attendance?
- How have repertoire and attendance changed over time?
- What role do co-productions play, and how does their reporting affect comparisons?

## Main findings

**TODO:** Add three to five findings after validating the final analysis. Include the period, measure, and any relevant limitation for each finding.

- **Production lifespan:** TODO
- **Performances and attendance:** TODO
- **Changes over time:** TODO

<!-- Optional: add a final dashboard screenshot here using a relative path. -->

## Deliverables

| Deliverable | Location |
|---|---|
| Final report | TODO: add repository-relative link |
| Power BI dashboard | TODO: add link to the .pbix file and/or published dashboard |
| Presentation | TODO: add repository-relative link |
| Data preparation scripts and SQL | TODO: add links to final files |

## Data sources

The project overview describes the following sources. Exact dataset links, versions, and access conditions will be documented before release.

| Source | Use in the project | Reference |
|---|---|---|
| Estonian Theatre Agency production and repertoire data | Production characteristics, repertoire, performances, attendance, and ticket revenue | TODO: dataset URLs, filenames, download dates |
| Detailed performance data supplied by the Estonian Theatre Agency | Additional production and performance information | TODO: describe coverage and whether files can be redistributed |
| Teatmik annual theatre data, 2014–2025 | Annual theatre information | TODO: exact source and files used |
| Estonian Business Register open data and annual reports | Theatre business entities and financial indicators | TODO: exact datasets and reporting periods |

Source files are primarily Excel workbooks. See `data/README.md` for acquisition instructions, field definitions, and which files are included or must be obtained separately. **TODO:** Create that document.

## Tools and workflow

1. **Python:** Read source files, clean and standardise text and dates, convert numeric fields, link records, and load prepared data.
2. **PostgreSQL:** Store prepared tables, apply corrections, and create analytical views and the reporting model.
3. **Power BI:** Explore the data and present measures and visualisations.

Preparation includes standardising production titles and author names, matching productions across sources, identifying co-productions, and deriving lifespan-related fields.

### Data model

The reporting model uses shared dimensions and fact tables. The implementation section of the project overview identifies these objects:

| Object | Purpose |
|---|---|
| `dim_lavastused` | Production identifiers, characteristics, co-production information, and lifespan fields |
| `dim_teater` | Theatre information and latest known ownership structure |
| `dim_saal` | Theatre/venue identifiers and seating capacity |
| `dim_aeg` | Calendar covering 2014–2025 |
| `fact_repertuaar` | Annual repertoire, performance, attendance, and ticket revenue measures |
| `fact_moodikud` | Metrics aggregated across the analysis period |
| `fact_majandusaasta_andmed` | Financial indicators from annual reports |

**TODO:** Confirm these names against the final SQL and Power BI model. Document each fact table's grain (what one row represents), keys, relationships, and aggregation rules in `docs/data_model.md`.

### Production lifespan

Lifespan describes the observed period from a production's premiere to its last recorded performance. The draft also describes a duration measured in years.

**TODO:** Specify the final formula, date/year precision, treatment of missing dates, and handling of productions still active in 2025. A last recorded performance within the dataset does not necessarily mean a production has ended.

## Repository structure

Proposed layout; adjust it to match the final files.

| Path | Contents |
|---|---|
| `README.md` | Project overview and reproduction instructions |
| `data/README.md` | Data sources, access instructions, and field descriptions |
| `data/raw/` | Unchanged source files approved for inclusion |
| `data/processed/` | Prepared data exports approved for inclusion |
| `scripts/` | Python import, cleaning, and transformation scripts |
| `sql/` | Database setup, corrections, and analytical views |
| `powerbi/` | Power BI report files |
| `docs/` | Data model, methodology, and metric definitions |
| `results/` | Exported figures and summary tables |
| `reports/` | Final report and presentation |
| `requirements.txt` | Python dependencies and versions |
| `.gitignore` | Files excluded from version control |
| `LICENSE` | Licence for the team's original work |

## Reproducing the analysis

**TODO:** Complete and test this section from a fresh clone before publication. The sequence below describes the intended workflow; exact commands remain to be added.

### Requirements

- Python: TODO version and dependency installation instructions.
- PostgreSQL: TODO version and database setup requirements.
- Power BI Desktop: TODO version used.
- Source data: See `data/README.md` once completed.

### Run order

1. Clone this repository and install the Python dependencies.
2. Obtain the required source workbooks and place them in the documented input directory.
3. Create the PostgreSQL database and configure the connection locally. The draft uses the schema `teatriliit`; confirm this in the final setup.
4. Run the Python import and cleaning script. The draft references `MAIN_teatri_excel_import.py`; add its final path and command here.
5. Execute the SQL corrections and reporting views. The draft references `MAIN_view.txt`; confirm the final SQL filename and execution order.
6. Open the Power BI report, configure its PostgreSQL connection, and refresh the data.

**TODO:** Document required configuration variables, input filenames, expected outputs, and any manual correction steps. Keep passwords and database credentials outside version-controlled files.

## Data quality and limitations

- **Inconsistent names:** Production titles, author names, and punctuation vary across sources. Cleaning and reference corrections support matching, but matching decisions can affect results.
- **Co-productions:** A production can belong to multiple theatres. These records cannot simply be removed as duplicates because they may retain meaningful theatre-level information.
- **Reporting changes:** The draft identifies inconsistent co-production attendance and performance reporting in 2014–2019, with more standardised reporting from 2020. Comparability and double-counting risks must be considered when aggregating these records.
- **Venue information:** Missing or inconsistent venue identifiers prevent reliable hall occupancy analysis in the current project.
- **Observation window:** The 2014–2025 period may omit activity before or after the available data. Observed lifespan should not automatically be interpreted as a production's complete lifetime.
- **Ownership over time:** The described theatre dimension uses the latest known ownership structure. Historical comparisons should account for this choice.

**TODO:** Link to the final methodology and document the co-production aggregation rules used in each measure.

## Team

| Team member | Contribution described in the project overview |
|---|---|
| Hannes Ruusmaa | Data engineering; Python, SQL, and Power BI |
| Raul Sõrmus | Data engineering; Python, SQL, and Power BI |
| Vesta Väljan | Data organisation; Python, SQL, and Power BI |
| Jandra Mölder | Project documentation and visualisation; Power BI |

**TODO:** Confirm final contributions and optionally add GitHub or LinkedIn profiles.

## Acknowledgements and licensing

This project was developed as part of the BCS data analysis microprogram. We acknowledge the Estonian Theatre Agency and the other data providers whose materials support the analysis.

**Project licence:** TODO: Select a licence for the team's original code and documentation and add the `LICENSE` file.

**Source data:** TODO: Record the applicable source terms and confirm which datasets can be redistributed. Specify source-data terms separately from the licence for the team's work.
