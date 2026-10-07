# DEGURBA-anchored city projections

Population, built-up area and urban area for 2030, 2040 and 2050.

## Contents of this folder

- **`degurba_projection_method.py`**: the Python script that carries out the method described below.
- **A Google Earth Engine (GEE) script** for viewing and downloading the data: https://code.earthengine.google.com/eae83081b123ec6fd2328b7ab51a7fb0. This GEE script is the code behind the AUG Explorer app: https://wri-datalab.earthengine.app/view/augexplorer.

### GEE assets with the projection data

The GEE script reads from two GEE feature collections:

- **`projects/wri-datalab/cities/urban_land_use/data/urbext_popdata_v3`**: the projection data. A table with one row per urban extent, identified by the field `id`. Fields are named `<source><variable>_<year>`, where the source prefix is `DEG`, `AUG` or `PLH`. The fields the script reads are:
  - `DEGpop`, `DEGbu`, `DEGdensbu`: DEGURBA series. `DEGdensbu` is read for 1990-2020 only.
  - `AUGpop`, `AUGarea`: AUG estimates, 1990-2020.
  - `AUGpop`, `AUGbu`: 2030, 2040 and 2050.
  - `PLHpop`, `PLHarea`: 2030, 2040 and 2050.
- **`projects/wri-datalab/cities/urban_land_use/data/global_GUPPD_Sept2025/urbanextents_unions_2020`**: the urban extent polygons for 2020, shown as the map layer. The script finds the polygon containing a clicked point and uses its `city_id_large` to look up the matching row (`id`) in the projection data table. The polygons also carry `city_name_large` and `country_name_large`.

## Purpose

For each city in an input table, the script produces projections to 2030, 2040 and 2050 of:

- population
- built-up area
- total urban area
- population density (per km² of built-up area, and per km² of urban area)

Each city has historical estimates for 1990-2020 of its urban extent from the Atlas of Urban Growth (AUG): population, built-up area and urban area. These are referred to below as the AUG estimates. The only forward-looking figures available are for a related spatial unit from the Degree of Urbanisation (DEGURBA) classification, whose series runs 1990-2050. The DEGURBA unit and the AUG urban extent cover somewhat different footprints, so the DEGURBA levels cannot be used as-is. What the script takes from the DEGURBA unit is its growth path, and it rescales that path to the AUG level. Where a city has no DEGURBA unit at all, it borrows a growth path from comparable DEGURBA units in the same country.

Every number in the input is a given. The script does not invent any population, built-up area or area figure; it only combines the figures you supply, using the arithmetic below.

## Method

Every city is handled by one of two tracks, chosen automatically.

### Track 1 (direct): the city has a DEGURBA unit with a usable series

The city's AUG estimates and the DEGURBA unit's historical numbers describe the same place on slightly different footprints. The ratio of their 1990-2020 averages measures that mismatch, and is used as a correction factor for each variable (population and built-up area):

```
CORR = average(AUG estimates for 1990, 2000, 2010, 2020)
       / average(DEGURBA unit's 1990, 2000, 2010, 2020 values)
```

The DEGURBA unit's 2030/2040/2050 figures are then multiplied by the correction factor:

```
PROJpop[year] = degurba_pop[year] * CORRpop
PROJbu[year]  = degurba_bu[year]  * CORRbu
```

Total urban area is not available for the DEGURBA unit. It is derived from the projected built-up area, assuming urban area stays proportional to built-up area at the AUG 1990-2020 average ratio:

```
PROJarea[year] = PROJbu[year] * (avg(area_1990..2020) / avg(bu_1990..2020))
```

Densities are population divided by built-up area, and population divided by urban area.

### Track 2 (fallback): the city has no usable DEGURBA unit

Without a DEGURBA series, there is nothing to rescale. Instead the city borrows a growth rate from DEGURBA units of similar size in the same country.

The **comparable units** are the DEGURBA units of the Track 1 cities in the same country. Those that are of similar size are the **matching units**. A comparable unit is a matching unit if its 2020 DEGURBA population (`degurba_pop_2020`) lies within a bracket around the Track 2 city's AUG 2020 population (`pop_2020`), set in log10 terms:

```
popmin = 10 ** (log10(pop_2020) - 0.3)
popmax = 10 ** (log10(pop_2020) + 0.3)
```

Since 10^0.3 is about 2, the bracket runs from roughly half to roughly double the city's AUG population. The half-width (0.3) can be changed with `--log-bracket`.

For each matching unit, growth ratios relative to the unit's own 2020 value are computed (for 2030, 2040 and 2050, for population and for built-up area):

```
degurba_pop[year] / degurba_pop[2020]
degurba_bu[year]  / degurba_bu[2020]
```

The ratios are averaged across all matching units (simple average, each unit counts equally), and applied to the city's AUG 2020 values:

```
PROJpop[year] = pop_2020 * average population ratio[year]
PROJbu[year]  = bu_2020  * average built-up ratio[year]
```

Urban area and densities are then derived exactly as in Track 1.

The comparable units come from the Track 1 cities in the same input file. Providing more Track 1 cities per country gives Track 2 cities more comparable units, and so more chances of finding matching units.

### Assumptions built into the method

- **Track 1:** the AUG estimates keep their 1990-2020 average relationship to the DEGURBA unit.
- **Track 2:** the city grows like the average same-country unit of similar size.
- **Both tracks:** urban area moves in proportion to built-up area, at the AUG 1990-2020 average ratio.

## Input CSV

One CSV, one row per city, with a header row. Track 1 and Track 2 cities go in the same file, in any order. Column names must match exactly (case-sensitive). Extra columns are allowed and are carried through to the output unchanged.

### Identifier columns

| Column | Required | Description |
|---|---|---|
| `city` | yes | City name (text). |
| `country` | yes | Country name (text). Used to match Track 2 cities to comparable units in the same country. Matching ignores case and leading/trailing spaces, but the spelling must otherwise agree across rows. |
| `city_id` | no | Passed through. |
| `region` | no | Passed through. |

### The city's AUG estimates (required for every city)

| Columns | Meaning |
|---|---|
| `pop_1990`, `pop_2000`, `pop_2010`, `pop_2020` | Population, persons |
| `bu_1990`, `bu_2000`, `bu_2010`, `bu_2020` | Built-up area, km² |
| `area_1990`, `area_2000`, `area_2010`, `area_2020` | Urban area, km² |

### The DEGURBA unit's series, 1990-2050

These 14 columns must exist in the file for every row:

| Columns | Meaning |
|---|---|
| `degurba_pop_1990`, `degurba_pop_2000`, `degurba_pop_2010`, `degurba_pop_2020`, `degurba_pop_2030`, `degurba_pop_2040`, `degurba_pop_2050` | DEGURBA unit population |
| `degurba_bu_1990`, `degurba_bu_2000`, `degurba_bu_2010`, `degurba_bu_2020`, `degurba_bu_2030`, `degurba_bu_2040`, `degurba_bu_2050` | DEGURBA unit built-up area |

- **Track 1 cities:** fill them in. A genuine zero (for example, 0 in 1990 because the unit had no population then) is entered as 0, not left blank.
- **Track 2 cities:** leave all 14 blank.

### Track assignment

Track assignment is automatic; the input has no track column.

- Track 1 if the mean of `degurba_pop_1990` to `degurba_pop_2020` is nonzero.
- Track 2 if it is zero or blank.

### Number format

Numbers must be plain: no thousands separators, no units. Blank means missing. A non-numeric entry in a numeric column stops the script with an error naming the column and the row.

## Output CSV

A CSV containing every input row (original order, original columns) plus the columns below.

| Column(s) | Description |
|---|---|
| `track` | 1 or 2 |
| `projection_method` | `direct` or `fallback` |
| `densbu_1990` to `densbu_2020` | `pop / bu` (blank if `bu` is 0) |
| `densarea_1990` to `densarea_2020` | `pop / area` (blank if `area` is 0) |
| `PROJpop_2030`, `PROJpop_2040`, `PROJpop_2050` | Projected population |
| `PROJbu_2030`, `PROJbu_2040`, `PROJbu_2050` | Projected built-up area |
| `PROJarea_2030`, `PROJarea_2040`, `PROJarea_2050` | Projected urban area |
| `PROJdensbu_2030`, `PROJdensbu_2040`, `PROJdensbu_2050` | `PROJpop / PROJbu` |
| `PROJdensarea_2030`, `PROJdensarea_2040`, `PROJdensarea_2050` | `PROJpop / PROJarea` |

Track 1 only (intermediate values):

| Column(s) | Description |
|---|---|
| `UAVGPOP`, `UAVGBU`, `UAVGAREA` | 1990-2020 averages of the AUG estimates |
| `DAVGPOP`, `DAVGBU` | DEGURBA unit's 1990-2020 averages |
| `CORRpop`, `CORRbu` | Correction factors |

Track 2 only (intermediate values):

| Column(s) | Description |
|---|---|
| `popmin`, `popmax` | The size bracket used |
| `n_reference_units` | Number of matching units (comparable units inside the size bracket) |
| `avg_pop_growth_2030`, `avg_pop_growth_2040`, `avg_pop_growth_2050` | Average population growth ratio across matching units |
| `avg_bu_growth_2030`, `avg_bu_growth_2040`, `avg_bu_growth_2050` | Average built-up area growth ratio across matching units |

Columns that apply to only one track are blank for the other track.

### Blank projection cells

A projection cell is blank when it cannot be computed, which happens when:

- a Track 2 city has no matching unit, i.e. no comparable unit within its size bracket (`n_reference_units` is 0);
- a divisor is zero (for example, a DEGURBA built-up average of 0 gives no built-up correction factor);
- a value needed for the city is blank.

A Track 1 city can therefore have population projections but blank built-up and area projections, if its DEGURBA built-up series averages 0 while its population series does not.

In the built-up growth average for Track 2, a matching unit whose `degurba_bu_2020` is 0 is skipped (its ratio is undefined); it is still used for the population average.
