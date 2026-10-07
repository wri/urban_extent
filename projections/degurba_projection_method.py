"""
DEGURBA-anchored city projections
Population, built-up area and urban area for 2030, 2040 and 2050


PURPOSE
--------------------------------
For each city in an input table, this script produces projections to 2030,
2040 and 2050 of:
    - population
    - built-up area
    - total urban area
    - population density (per km^2 of built-up area, and per km^2 of
      urban area)

Each city has historical estimates for 1990-2020 of its urban extent from
the Atlas of Urban Growth (AUG): population, built-up area and urban
area. These are referred to below as the AUG estimates. The only
forward-looking figures available are for a related spatial unit from the
Degree of Urbanisation (DEGURBA) classification, whose series runs
1990-2050. The DEGURBA unit and the AUG urban extent cover somewhat
different footprints, so the DEGURBA levels cannot be used as-is. What the
script takes from the DEGURBA unit is its growth path, and it rescales
that path to the AUG level. Where a city has no DEGURBA unit at all, it
borrows a growth path from comparable DEGURBA units in the same country.

Every number in the input is a given. The script does not invent any
population, built-up area or area figure; it only combines the figures you
supply, using the arithmetic below.


THE METHOD
--------------------------------
Every city is handled by one of two tracks, chosen automatically.

TRACK 1 (direct) -- the city has a DEGURBA unit with a usable series.

   The city's AUG estimates and the DEGURBA unit's historical numbers
   describe the same place on slightly different footprints. The ratio of
   their 1990-2020 averages measures that mismatch, and is used as a
   correction factor for each variable (population and built-up area):

       CORR = average(AUG estimates for 1990, 2000, 2010, 2020)
              / average(DEGURBA unit's 1990, 2000, 2010, 2020 values)

   The DEGURBA unit's 2030/2040/2050 figures are then multiplied by the
   correction factor:

       PROJpop[year] = degurba_pop[year] * CORRpop
       PROJbu[year]  = degurba_bu[year]  * CORRbu

   Total urban area is not available for the DEGURBA unit. It is derived
   from the projected built-up area, assuming urban area stays
   proportional to built-up area at the AUG 1990-2020 average ratio:

       PROJarea[year] = PROJbu[year] * (avg(area_1990..2020) / avg(bu_1990..2020))

   Densities are population divided by built-up area, and population
   divided by urban area.

TRACK 2 (fallback) -- the city has no usable DEGURBA unit.

   Without a DEGURBA series, there is nothing to provide direct scaling
   factors. Instead, the city borrows a growth rate from DEGURBA units
   of similar size in the same country.

   The "comparable units" are the DEGURBA units of the Track 1 cities in
   the same country. Those that are of similar size are the "matching
   units". A comparable unit is a matching unit if its 2020 DEGURBA
   population (degurba_pop_2020) lies within a bracket around the Track 2
   city's AUG 2020 population (pop_2020), set in log10 terms:

       popmin = 10 ** (log10(pop_2020) - 0.3)
       popmax = 10 ** (log10(pop_2020) + 0.3)

   Since 10**0.3 is about 2, the bracket runs from roughly half to
   roughly double the city's AUG population. The half-width (0.3) can be
   changed with --log-bracket.

   For each matching unit, growth ratios relative to the unit's own 2020 value
   are computed (for 2030, 2040 and 2050, for population and for built-up
   area):

       degurba_pop[year] / degurba_pop[2020]
       degurba_bu[year]  / degurba_bu[2020]

   The ratios are averaged across all matching units (simple average,
   each unit counts equally), and applied to the city's AUG 2020 values:

       PROJpop[year] = pop_2020 * average population ratio[year]
       PROJbu[year]  = bu_2020  * average built-up ratio[year]

   Urban area and densities are then derived exactly as in Track 1.

The comparable units come from the Track 1 cities in the same input file.
Providing more Track 1 cities per country gives Track 2 cities more
comparable units, and so more chances of finding matching units.

Assumptions built into the method:
    - Track 1: the AUG estimates keep their 1990-2020 average
      relationship to the DEGURBA unit.
    - Track 2: the city grows like the average same-country unit of
      similar size.
    - Both tracks: urban area moves in proportion to built-up area, at the
      AUG 1990-2020 average ratio.


WORKFLOW
--------------------------------
1. Build one CSV with one row per city (format below). Include both
   cities that have a DEGURBA series (Track 1) and cities that do not
   (Track 2) in the same file.
2. Run:
       python degurba_projection_method.py input.csv output.csv
       python degurba_projection_method.py input.csv output.csv --log-bracket 0.3
   or from Python:
       from degurba_projection_method import run
       result_df = run("input.csv", "output.csv")
3. Read the summary printed at the end: how many cities went to each
   track, and a warning if some Track 2 cities found no matching units.
4. Use the output CSV. It contains every input row plus the projections
   and the intermediate quantities, so any city's result can be traced.


INPUT FORMAT
--------------------------------
One CSV, one row per city, with a header row. Track 1 and Track 2 cities
go in the same file, in any order. Column names must match exactly
(case-sensitive). Extra columns are allowed and are carried through to the
output unchanged.

Identifier columns:
    city        required   city name (text)
    country     required   country name (text). Used to match Track 2
                           cities to comparable units in the same
                           country. Matching ignores case and
                           leading/trailing spaces, but the spelling must
                           otherwise agree across rows.
    city_id     optional   passed through
    region      optional   passed through

The city's AUG estimates, required for EVERY city:
    pop_1990,  pop_2000,  pop_2010,  pop_2020     persons
    bu_1990,   bu_2000,   bu_2010,   bu_2020      built-up area, km^2
    area_1990, area_2000, area_2010, area_2020    urban area, km^2

The DEGURBA unit's series, 1990-2050. These 14 columns must exist in the
file for every row:
    degurba_pop_1990, degurba_pop_2000, degurba_pop_2010, degurba_pop_2020,
    degurba_pop_2030, degurba_pop_2040, degurba_pop_2050
    degurba_bu_1990,  degurba_bu_2000,  degurba_bu_2010,  degurba_bu_2020,
    degurba_bu_2030,  degurba_bu_2040,  degurba_bu_2050
  - Track 1 cities: fill them in. A genuine zero (for example, 0 in 1990
    because the unit had no population then) is entered as 0, not left
    blank.
  - Track 2 cities: leave all 14 blank.

Track assignment is automatic; the input has no track column:
    Track 1 if the mean of degurba_pop_1990..2020 is nonzero.
    Track 2 if it is zero or blank.

Numbers must be plain: no thousands separators, no units. Blank means
missing. A non-numeric entry in a numeric column stops the script with an
error naming the column and the row.


OUTPUT FORMAT
--------------------------------
A CSV containing every input row (original order, original columns) plus:
    track                          1 or 2
    projection_method              "direct" or "fallback"
    densbu_1990..2020              pop / bu   (blank if bu is 0)
    densarea_1990..2020            pop / area (blank if area is 0)
    PROJpop_2030/2040/2050
    PROJbu_2030/2040/2050
    PROJarea_2030/2040/2050
    PROJdensbu_2030/2040/2050      PROJpop / PROJbu
    PROJdensarea_2030/2040/2050    PROJpop / PROJarea
    Track 1 only (intermediate values):
        UAVGPOP, UAVGBU, UAVGAREA  1990-2020 averages of the AUG estimates
        DAVGPOP, DAVGBU            DEGURBA unit's 1990-2020 averages
        CORRpop, CORRbu            correction factors
    Track 2 only (intermediate values):
        popmin, popmax             the size bracket used
        n_reference_units          number of matching units (comparable
                                   units inside the size bracket)
        avg_pop_growth_2030/2040/2050
        avg_bu_growth_2030/2040/2050

Columns that apply to only one track are blank for the other track.

A projection cell is blank when it cannot be computed, which happens when:
    - a Track 2 city has no matching unit, i.e. no comparable unit
      within its size bracket (n_reference_units is 0);
    - a divisor is zero (for example a DEGURBA built-up average of 0 gives
      no built-up correction factor);
    - a value needed for the city is blank.

A Track 1 city can therefore have population projections but blank
built-up and area projections, if its DEGURBA built-up series averages 0
while its population series does not.

In the built-up growth average for Track 2, a matching unit whose
degurba_bu_2020 is 0 is skipped (its ratio is undefined); it is still
used for the population average.
"""

import argparse
import math
import sys

import numpy as np
import pandas as pd

HIST_YEARS = (1990, 2000, 2010, 2020)
PROJ_YEARS = (2030, 2040, 2050)
ALL_YEARS = HIST_YEARS + PROJ_YEARS

# Half-width, in log10(population), of the size bracket used to pick
# matching units from the comparable units for Track 2. 0.3 in log10 space is a factor of about 2
# (10**0.3 ~ 1.995), so the bracket is approximately
# [pop_2020 / 2, pop_2020 * 2].
DEFAULT_LOG_BRACKET = 0.3

CITY_COLS = (
    [f"pop_{y}" for y in HIST_YEARS]
    + [f"bu_{y}" for y in HIST_YEARS]
    + [f"area_{y}" for y in HIST_YEARS]
)
DEGURBA_COLS = (
    [f"degurba_pop_{y}" for y in ALL_YEARS]
    + [f"degurba_bu_{y}" for y in ALL_YEARS]
)
NUMERIC_COLS = CITY_COLS + DEGURBA_COLS
REQUIRED_COLS = ["city", "country"] + NUMERIC_COLS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def safe_div(a, b):
    """a / b, giving NaN (a blank cell in the output) wherever b is 0 or NaN."""
    return a / b.where(b != 0)


def load_input(path: str) -> pd.DataFrame:
    """Read the CSV and check it against the format described above."""
    df = pd.read_csv(path)

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Input is missing required column(s): {missing}")

    for col in NUMERIC_COLS:
        converted = pd.to_numeric(df[col], errors="coerce")
        bad = converted.isna() & df[col].notna()
        if bad.any():
            first = bad.idxmax()
            raise ValueError(
                f"Non-numeric value {df.loc[first, col]!r} in column '{col}' "
                f"(first occurrence at data row {first + 1})."
            )
        df[col] = converted

    # Matching key for country (ignores case and surrounding spaces).
    df["_country_key"] = df["country"].astype(str).str.strip().str.lower()
    return df


def historical_densities(df: pd.DataFrame) -> pd.DataFrame:
    """densbu_y = pop_y / bu_y and densarea_y = pop_y / area_y, 1990-2020."""
    out = {}
    for y in HIST_YEARS:
        out[f"densbu_{y}"] = safe_div(df[f"pop_{y}"], df[f"bu_{y}"])
        out[f"densarea_{y}"] = safe_div(df[f"pop_{y}"], df[f"area_{y}"])
    return pd.DataFrame(out, index=df.index)


def add_density_projections(out: pd.DataFrame) -> None:
    for y in PROJ_YEARS:
        out[f"PROJdensbu_{y}"] = safe_div(out[f"PROJpop_{y}"], out[f"PROJbu_{y}"])
        out[f"PROJdensarea_{y}"] = safe_div(out[f"PROJpop_{y}"], out[f"PROJarea_{y}"])


# ---------------------------------------------------------------------------
# Track 1: direct, DEGURBA-anchored method
# ---------------------------------------------------------------------------

def direct_projection(df: pd.DataFrame) -> pd.DataFrame:
    """
    Track 1 calculation. `df` holds only Track 1 rows. Returns a frame
    (same index) of the computed columns only.
    """
    pop_hist = [f"pop_{y}" for y in HIST_YEARS]
    bu_hist = [f"bu_{y}" for y in HIST_YEARS]
    area_hist = [f"area_{y}" for y in HIST_YEARS]
    dpop_hist = [f"degurba_pop_{y}" for y in HIST_YEARS]
    dbu_hist = [f"degurba_bu_{y}" for y in HIST_YEARS]

    # "U" = averages of the AUG estimates; "D" = averages of the DEGURBA series.
    out = pd.DataFrame(index=df.index)
    out["UAVGPOP"] = df[pop_hist].mean(axis=1)
    out["DAVGPOP"] = df[dpop_hist].mean(axis=1)
    out["UAVGBU"] = df[bu_hist].mean(axis=1)
    out["DAVGBU"] = df[dbu_hist].mean(axis=1)
    out["UAVGAREA"] = df[area_hist].mean(axis=1)

    out["CORRpop"] = safe_div(out["UAVGPOP"], out["DAVGPOP"])
    out["CORRbu"] = safe_div(out["UAVGBU"], out["DAVGBU"])

    area_per_bu = safe_div(out["UAVGAREA"], out["UAVGBU"])

    for y in PROJ_YEARS:
        out[f"PROJpop_{y}"] = df[f"degurba_pop_{y}"] * out["CORRpop"]
        out[f"PROJbu_{y}"] = df[f"degurba_bu_{y}"] * out["CORRbu"]
        out[f"PROJarea_{y}"] = out[f"PROJbu_{y}"] * area_per_bu

    add_density_projections(out)
    return out


# ---------------------------------------------------------------------------
# Comparable units for Track 2
# ---------------------------------------------------------------------------

def build_growth_rate_pool(track1: pd.DataFrame) -> dict:
    """
    From the Track 1 rows, build, per country, the comparable units that
    Track 2 draws on: each unit's degurba_pop_2020 and its growth ratios relative to 2020
    (for 2030, 2040, 2050) for population and built-up area.

    Returns {country_key: {"pop2020": array, "GRpop": {year: array},
                           "GRbu": {year: array}}}
    """
    pool = {}
    for key, g in track1.groupby("_country_key"):
        entry = {
            "pop2020": g["degurba_pop_2020"].to_numpy(dtype=float),
            "GRpop": {},
            "GRbu": {},
        }
        for y in PROJ_YEARS:
            entry["GRpop"][y] = safe_div(
                g[f"degurba_pop_{y}"], g["degurba_pop_2020"]
            ).to_numpy(dtype=float)
            entry["GRbu"][y] = safe_div(
                g[f"degurba_bu_{y}"], g["degurba_bu_2020"]
            ).to_numpy(dtype=float)
        pool[key] = entry
    return pool


# ---------------------------------------------------------------------------
# Track 2: fallback, same-country and size-matched growth rates
# ---------------------------------------------------------------------------

def fallback_projection(
    df: pd.DataFrame, pool: dict, log_bracket: float = DEFAULT_LOG_BRACKET
) -> pd.DataFrame:
    """
    Track 2 calculation. `df` holds only Track 2 rows. Returns a frame
    (same index) of the computed columns only.
    """
    n = len(df)
    popmin = np.full(n, np.nan)
    popmax = np.full(n, np.nan)
    n_ref = np.zeros(n, dtype=int)
    avg_pop = {y: np.full(n, np.nan) for y in PROJ_YEARS}
    avg_bu = {y: np.full(n, np.nan) for y in PROJ_YEARS}

    pop2020 = df["pop_2020"].to_numpy(dtype=float)
    keys = df["_country_key"].to_numpy()

    for i in range(n):
        p = pop2020[i]
        if not (p > 0):  # NaN or <= 0: log10 undefined, no bracket
            continue
        lo = 10 ** (math.log10(p) - log_bracket)
        hi = 10 ** (math.log10(p) + log_bracket)
        popmin[i], popmax[i] = lo, hi

        entry = pool.get(keys[i])
        if entry is None:
            continue
        mask = (entry["pop2020"] >= lo) & (entry["pop2020"] <= hi)
        n_ref[i] = int(mask.sum())
        if n_ref[i] == 0:
            continue
        for y in PROJ_YEARS:
            gp = entry["GRpop"][y][mask]
            gb = entry["GRbu"][y][mask]
            if (~np.isnan(gp)).any():
                avg_pop[y][i] = np.nanmean(gp)
            if (~np.isnan(gb)).any():
                avg_bu[y][i] = np.nanmean(gb)

    out = pd.DataFrame(index=df.index)
    out["popmin"], out["popmax"], out["n_reference_units"] = popmin, popmax, n_ref

    area_per_bu = safe_div(
        df[[f"area_{y}" for y in HIST_YEARS]].mean(axis=1),
        df[[f"bu_{y}" for y in HIST_YEARS]].mean(axis=1),
    )

    for y in PROJ_YEARS:
        out[f"avg_pop_growth_{y}"] = avg_pop[y]
        out[f"avg_bu_growth_{y}"] = avg_bu[y]
    for y in PROJ_YEARS:
        out[f"PROJpop_{y}"] = df["pop_2020"] * out[f"avg_pop_growth_{y}"]
        out[f"PROJbu_{y}"] = df["bu_2020"] * out[f"avg_bu_growth_{y}"]
        out[f"PROJarea_{y}"] = out[f"PROJbu_{y}"] * area_per_bu

    add_density_projections(out)
    return out


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def run(input_path: str, output_path: str, log_bracket: float = DEFAULT_LOG_BRACKET):
    df = load_input(input_path)

    # Track assignment: Track 1 if the mean of degurba_pop_1990..2020 is nonzero.
    dpop_avg = df[[f"degurba_pop_{y}" for y in HIST_YEARS]].mean(axis=1)
    is_track1 = dpop_avg.notna() & (dpop_avg != 0)

    track1 = df[is_track1]
    track2 = df[~is_track1]

    parts = []
    if len(track1):
        t1 = direct_projection(track1)
        t1["track"] = 1
        t1["projection_method"] = "direct"
        parts.append(t1)
    if len(track2):
        pool = build_growth_rate_pool(track1)
        t2 = fallback_projection(track2, pool, log_bracket=log_bracket)
        t2["track"] = 2
        t2["projection_method"] = "fallback"
        parts.append(t2)

    computed = pd.concat(parts).sort_index()
    computed = computed.join(historical_densities(df))

    # Output: original columns (minus the internal key), then computed.
    result = pd.concat([df.drop(columns=["_country_key"]), computed], axis=1)
    result.to_csv(output_path, index=False)

    # Summary
    print(f"Read {len(df)} cities: {len(track1)} Track 1 (direct), "
          f"{len(track2)} Track 2 (fallback).")
    if len(track2):
        no_ref = int((computed.loc[track2.index, "n_reference_units"] == 0).sum())
        if no_ref:
            print(f"WARNING: {no_ref} Track 2 cities had no matching unit "
                  f"(no same-country comparable unit within the size "
                  f"bracket); their projections are blank.")
    print(f"Wrote {output_path}")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("WORKFLOW")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input_csv")
    ap.add_argument("output_csv")
    ap.add_argument("--log-bracket", type=float, default=DEFAULT_LOG_BRACKET,
                    help="half-width of the size bracket in log10 units "
                         "(default 0.3)")
    args = ap.parse_args()
    try:
        run(args.input_csv, args.output_csv, args.log_bracket)
    except ValueError as e:
        sys.exit(f"Input error: {e}")
