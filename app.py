"""
Airport Details Finder - Streamlit Web App
============================================
A web app that lets users search for airport details by name, IATA code,
ICAO code, city, or country, shows them on an interactive map,
and displays full details.

Run with:  streamlit run app.py
"""

import folium
import pandas as pd
import pycountry
import streamlit as st

# CSV file from OurAirports: https://davidmegginson.github.io/ourairports-data/
DATA_FILE = "data/airports.csv"

# Fields that are searchable (country_name is derived from iso_country;
# keywords holds alternate/old names, e.g. 'Katunayake' for Colombo airport)
SEARCH_COLUMNS = ["name", "iata_code", "icao_code", "municipality",
                  "iso_country", "country_name", "keywords"]

# Max airports plotted on the map (keeps the map fast & readable)
MAX_MAP_MARKERS = 500


@st.cache_data
def load_airports(file_path):
    """
    Load the airports CSV once and prepare it for fast searching:
      - everything read as string, empty cells as ""
      - coordinates converted to numbers
      - country names derived from ISO codes (so 'srilanka' finds 'LK')
      - pre-lowercased search columns + one combined search text (fast search)
    Cached: the 13 MB file is read only once, no matter how many searches.
    """
    df = pd.read_csv(file_path, dtype=str, keep_default_na=False)
    df = df.fillna("")

    # Convert coordinates to numbers (invalid values become NaN -> excluded from map)
    for col in ["latitude_deg", "longitude_deg"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Build a country-code -> country-name mapping for the codes in the dataset
    name_map = {}
    for code in df["iso_country"].unique():
        if code:
            country = pycountry.countries.get(alpha_2=code)
            name_map[code] = country.name if country else code
    df["country_name"] = df["iso_country"].map(name_map).fillna(df["iso_country"])

    # Pre-lowercase all search fields once -> searches are a single fast pass
    for col in SEARCH_COLUMNS:
        df[f"_lc_{col}"] = df[col].astype(str).str.lower()

    # Also a space-stripped country name, so 'srilanka' matches 'Sri Lanka'
    df["_lc_country_nospace"] = df["_lc_country_name"].str.replace(" ", "")

    # One combined search text per airport (used for the "All fields" search)
    df["_search_all"] = (
        df["_lc_name"] + " | " +
        df["_lc_iata_code"] + " | " +
        df["_lc_icao_code"] + " | " +
        df["_lc_municipality"] + " | " +
        df["_lc_iso_country"] + " | " +
        df["_lc_country_name"] + " | " +
        df["_lc_country_nospace"] + " | " +
        df["_lc_keywords"]
    )

    return df


def search_airports(airports_df, query, field):
    """
    Find airports matching the query.

    - field: which column to search ('all', 'name', 'iata_code', 'icao_code',
             'municipality', 'iso_country', 'country_name')
    - query: search term, case-insensitive, partial match
    - Matches are OR'd across fields (a result only needs to match ONE field),
      which is what makes searching 'CMB' (IATA-only) work correctly.
    """
    query = query.strip().lower()
    if not query:
        return airports_df.iloc[0:0]  # empty result

    if field == "all":
        mask = airports_df["_search_all"].str.contains(query, regex=False)
    else:
        mask = airports_df[f"_lc_{field}"].str.contains(query, regex=False)

    result = airports_df[mask]

    # Remove duplicate entries (same airport listed under several codes)
    if "ident" in result.columns:
        result = result.drop_duplicates(subset=["ident"])

    # Sort for relevance: exact IATA match first, then exact ICAO,
    # then name starting with the query, then the rest
    if not result.empty:
        exact_iata = result["_lc_iata_code"] == query
        exact_icao = result["_lc_icao_code"] == query
        name_starts = result["_lc_name"].str.startswith(query)
        result = result.assign(
            _score=(3 * exact_iata + 2 * exact_icao + 1 * name_starts).astype(int)
        ).sort_values("_score", ascending=False).drop(columns=["_score"])

    return result.reset_index(drop=True)


def build_map(matches):
    """
    Build an interactive Folium map with one marker per airport.
    Each marker shows the airport name in a tooltip and full details in a popup.
    Returns the map as HTML, or None if there are no plotable results.
    """
    # Only airports with valid coordinates can be plotted
    valid = matches.dropna(subset=["latitude_deg", "longitude_deg"])
    valid = valid[
        valid["latitude_deg"].between(-90, 90) &
        valid["longitude_deg"].between(-180, 180)
    ]
    if valid.empty:
        return None, 0

    plotted = valid.head(MAX_MAP_MARKERS)
    truncated = len(valid) - len(plotted)

    lats = plotted["latitude_deg"].tolist()
    lons = plotted["longitude_deg"].tolist()
    center = [sum(lats) / len(lats), sum(lons) / len(lons)]

    fm = folium.Map(location=center, zoom_start=5, tiles="OpenStreetMap")

    for _, ap in plotted.iterrows():
        name = ap.get("name", "Unknown airport")
        iata = ap.get("iata_code", "") or "N/A"
        icao = ap.get("icao_code", "") or "N/A"
        city = ap.get("municipality", "") or "N/A"
        country = ap.get("country_name", "") or ap.get("iso_country", "N/A")

        popup_html = (
            f"<div style='font-family: Arial; font-size: 13px;'>"
            f"<b>{name}</b><br>"
            f"IATA: {iata} | ICAO: {icao}<br>"
            f"City: {city}<br>"
            f"Country: {country}<br>"
            f"Lat: {ap['latitude_deg']:.4f}, Lon: {ap['longitude_deg']:.4f}"
            f"</div>"
        )
        folium.CircleMarker(
            location=[ap["latitude_deg"], ap["longitude_deg"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=name,
            radius=7,
            color="#d9534f",
            fill=True,
            fill_color="#d9534f",
            fill_opacity=0.7,
        ).add_to(fm)

    # Fit the map zoom to the plotted airports
    fm.fit_bounds([
        [min(lats), min(lons)],
        [max(lats), max(lons)],
    ])

    return fm.get_root().render(), truncated


def main():
    st.set_page_config(page_title="Airport Details Finder", page_icon="✈️", layout="centered")

    st.title("✈️ Airport Details Finder")
    st.markdown(
        "Search **over 86,000 airports** worldwide by name, IATA code, ICAO code, "
        "city, or country — see them on an **interactive map** and view full details."
    )
    st.divider()

    # --- Sidebar: search controls ---
    st.sidebar.header("Search Settings")
    query = st.sidebar.text_input(
        "Search term",
        placeholder="e.g. CMB, Colombo, Sri Lanka, Katunayake...",
        help="Case-insensitive. Partial matches work too.",
    )
    field = st.sidebar.selectbox(
        "Search by",
        options=["all", "name", "iata_code", "icao_code", "municipality",
                 "iso_country", "country_name"],
        format_func=lambda x: {
            "all": "All fields",
            "name": "Airport name",
            "iata_code": "IATA code",
            "icao_code": "ICAO code",
            "municipality": "City",
            "iso_country": "Country code (e.g. LK)",
            "country_name": "Country name (e.g. Sri Lanka)",
        }[x],
        index=0,
    )

    # --- Load data (with friendly error if the CSV is missing) ---
    try:
        airports_df = load_airports(DATA_FILE)
    except FileNotFoundError:
        st.error(
            f"❌ `{DATA_FILE}` not found!\n\n"
            "Download it from **OurAirports** and place it next to this file:\n"
            "https://davidmegginson.github.io/ourairports-data/"
        )
        st.stop()

    st.caption(f"📊 Dataset loaded: **{len(airports_df):,} airports**")

    # --- Search & results ---
    if st.sidebar.button("🔍 Search", type="primary") or query:
        matches = search_airports(airports_df, query, field)

        if matches.empty:
            st.warning(f"No airports found matching **'{query}'**. Try a different search term.")
        else:
            st.success(f"Found **{len(matches)}** airport(s) matching **'{query}'**")

            # 1. Interactive map
            st.subheader("🗺️ Airports on Map")
            map_html, truncated = build_map(matches)
            if map_html is None:
                st.info("No plotable locations (missing coordinates) for these results.")
            else:
                st.iframe(map_html, height=550)
                if truncated > 0:
                    st.caption(
                        f"ℹ️ Showing the first {MAX_MAP_MARKERS} airports on the map "
                        f"({truncated} more in the table below)."
                    )

            # 2. Detailed view: one expandable card per airport
            st.subheader("📋 Airport Details")
            for _, ap in matches.iterrows():
                with st.expander(f"{ap.get('name', 'Unknown airport')} "
                                 f"({ap.get('iata_code', 'N/A')})"):
                    col1, col2 = st.columns(2)
                    col1.markdown(f"**IATA Code:** `{ap.get('iata_code', 'N/A')}`")
                    col1.markdown(f"**ICAO Code:** `{ap.get('icao_code', 'N/A')}`")
                    col2.markdown(f"**City:** {ap.get('municipality', 'N/A')}")
                    col2.markdown(f"**Country:** {ap.get('country_name', ap.get('iso_country', 'N/A'))}")
                    col1.markdown(f"**Latitude:** {ap.get('latitude_deg', 'N/A')}")
                    col1.markdown(f"**Longitude:** {ap.get('longitude_deg', 'N/A')}")
                    col2.markdown(f"**Altitude:** {ap.get('elevation_ft', 'N/A')} ft")
                    col2.markdown(f"**Timezone:** {ap.get('tz', 'N/A')}")
                    st.markdown(f"**Type:** {ap.get('type', 'N/A')}")

            # 3. Full results table
            st.subheader("📊 All Results")
            show_cols = ["name", "iata_code", "icao_code", "municipality",
                         "country_name", "latitude_deg", "longitude_deg", "tz"]
            show_cols = [c for c in show_cols if c in matches.columns]
            st.dataframe(matches[show_cols].rename(columns={
                "name": "Airport", "iata_code": "IATA", "icao_code": "ICAO",
                "municipality": "City", "country_name": "Country",
                "latitude_deg": "Latitude", "longitude_deg": "Longitude", "tz": "Timezone"
            }), width='stretch')

    else:
        st.info("👆 Enter a search term in the sidebar and click **Search** to find airports.")
        # Show a small sample so the app isn't empty on first load
        st.markdown("### 👋 Preview of the dataset")
        sample = airports_df.head(5)[
            ["name", "iata_code", "icao_code", "municipality", "country_name"]
        ].rename(columns={
            "name": "Airport", "iata_code": "IATA", "icao_code": "ICAO",
            "municipality": "City", "country_name": "Country"
        })
        st.dataframe(sample, width='stretch')


if __name__ == "__main__":
    main()
