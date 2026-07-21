#!/usr/bin/env python3

"""Create a static Leaflet/Folium map from a sites.tsv file.

This script is a reconstruction of the missing `sites_create_map.py` from the
provided generated `map.html`. It reads a tab-separated file named `sites.tsv`
and writes `map.html`.

Expected TSV content
--------------------
The script is deliberately tolerant about column names. It looks for latitude
and longitude columns using common aliases, for example:

    latitude / lat / y / northing
    longitude / lon / lng / long / x / easting

Optional columns used when present:

    site / site_name / nom_site / name / context_name  -> marker label
    category / type / typology / categorie             -> marker category

Usage
-----
    python sites_create_map.py
    python sites_create_map.py --input sites.tsv --output map.html
    python sites_create_map.py --input sites.tsv --output C:/Users/TH282424/Rprojects/almacir/static/map.html
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path
from typing import Iterable

import folium
import pandas as pd

# Parameters visible in the recovered map.html
# DEFAULT_CENTER = [39.0, 12.0]
# 29.223574657146845, 18.155502558308747
DEFAULT_BOUNDS = [[29, -11], [44, 18]]
DEFAULT_CENTER = sum(DEFAULT_BOUNDS[0]) / 2, sum(DEFAULT_BOUNDS[1]) / 2
DEFAULT_ZOOM = 10
TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}"
TILE_ATTRIBUTION = "Tiles &copy; Esri &mdash; Source: US National Park Service"

# A small categorical palette for site categories. Folium/Leaflet will accept
# CSS color names or hex values.
CATEGORY_COLORS = {
    "or": "#D4AF37",      # gold
    "argent": "#C0C0C0",  # silver
}


def find_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    """Return the first matching column, case-insensitively."""
    columns = list(columns)
    lower_to_original = {c.lower().strip(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in lower_to_original:
            return lower_to_original[candidate.lower()]
    return None


def detect_columns(df: pd.DataFrame) -> tuple[str, str, str | None, str | None]:
    """Detect longitude, latitude, name, and category columns in sites.tsv."""
    lat_col = find_column(
        df.columns,
        ["latitude", "lat", "y", "northing", "lat_wgs84", "latitude_wgs84"],
    )
    lon_col = find_column(
        df.columns,
        ["longitude", "lon", "lng", "long", "x", "easting", "lon_wgs84", "longitude_wgs84"],
    )
    name_col = find_column(
        df.columns,
        ["site", "site_name", "nom_site", "name", "context_name", "label", "id"],
    )
    category_col = find_column(
        df.columns,
        ["category", "categorie", "type", "typology", "class", "period", "chronology"],
    )

    if lat_col is None or lon_col is None:
        raise ValueError(
            "Could not detect latitude/longitude columns in sites.tsv. "
            "Expected columns such as 'latitude'/'longitude', 'lat'/'lon', "
            "or 'northing'/'easting'."
        )

    return lon_col, lat_col, name_col, category_col


def make_popup(row: pd.Series, name_col: str | None, category_col: str | None) -> str:
    """Create an HTML popup for one site."""
    title = "Site"
    if name_col and pd.notna(row.get(name_col)):
        title = str(row[name_col])

    lines = [f"<strong>{html.escape(title)}</strong>"]
    if category_col and pd.notna(row.get(category_col)):
        lines.append(f"Catégorie: {html.escape(str(row[category_col]))}")

    return "<br>".join(lines)


def build_legend(category_to_color: dict[str, str]) -> str:
    """Build the fixed legend block found in the recovered map."""
    items = []
    for category, color in category_to_color.items():
        items.append(
            f"""
  <div style=\"display:flex; align-items:center; gap:6px; margin:2px 0;\">
    <span style=\"display:inline-block; width:11px; height:11px; border-radius:50%; background:{html.escape(color)}; border:1px solid #555;\"></span>
    <span>{html.escape(category)}</span>
  </div>"""
        )

    return f"""
<div id=\"map-legend\" style=\"
    position: fixed;
    bottom: 30px;
    left: 30px;
    z-index: 9999;
    background: white;
    padding: 10px 15px;
    border-radius: 4px;
    box-shadow: 0 0 8px rgba(0,0,0,0.15);
    font-size: 14px;
    \">
  <div style=\"font-weight:bold; margin-bottom:5px;\">Ateliers monétaires</div>
  {''.join(items)}
</div>
"""


def create_map(input_path: Path, output_path: Path) -> None:
    """Read sites.tsv and save a Folium/Leaflet map."""
    df = pd.read_csv(input_path, sep="\t")
    lon_col, lat_col, name_col, category_col = detect_columns(df)

    # Force numeric coordinates and drop rows without valid coordinates.
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
    df = df.dropna(subset=[lon_col, lat_col]).copy()

    m = folium.Map(
        location=DEFAULT_CENTER,
        zoom_start=DEFAULT_ZOOM,
        max_bounds=True,
        min_lat=DEFAULT_BOUNDS[0][0],
        max_lat=DEFAULT_BOUNDS[1][0],
        min_lon=DEFAULT_BOUNDS[0][1],
        max_lon=DEFAULT_BOUNDS[1][1],
        zoom_control=False,
        dragging=False,
        scrollWheelZoom=False,
        doubleClickZoom=False,
        touchZoom=False,
        tiles=None,
    )

    folium.TileLayer(
        tiles=TILE_URL,
        attr=TILE_ATTRIBUTION,
        min_zoom=5,
        max_zoom=5,
        max_native_zoom=5,
        name="Esri World Physical Map",
    ).add_to(m)

    category_to_color: dict[str, str] = {}
    if category_col:
        categories = sorted(str(v) for v in df[category_col].dropna().unique())
        category_to_color = {
            category: CATEGORY_COLORS.get(category.lower(), "#666666")
            for category in categories
        }

    for _, row in df.iterrows():
        category = str(row[category_col]) if category_col and pd.notna(row.get(category_col)) else "Site"
        color = category_to_color.get(category, "blue")
        tooltip = str(row[name_col]) if name_col and pd.notna(row.get(name_col)) else category

        folium.CircleMarker(
            location=[float(row[lat_col]), float(row[lon_col])],
            radius=6,
            popup=folium.Popup(make_popup(row, name_col, category_col), max_width=300),
            tooltip=tooltip,
            color="#333333",      # border
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=1,
        ).add_to(m)

    # Keep the same legend structure visible in the recovered HTML. If there are
    # no categories, this produces only the title, as in the uploaded map.html.
    m.get_root().html.add_child(folium.Element(build_legend(category_to_color)))

    m.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create map.html from sites.tsv")
    parser.add_argument("--input", "-i", default="sites.tsv", type=Path, help="Input TSV file")
    parser.add_argument("--output", "-o", default="map.html", type=Path, help="Output HTML file")
    args = parser.parse_args()

    create_map(args.input, args.output)
    print(f"Map written to {args.output}")


if __name__ == "__main__":
    main()
