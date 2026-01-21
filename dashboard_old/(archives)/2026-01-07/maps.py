from dash import html
import folium
from folium.plugins import MarkerCluster, Draw
from get_data import get_data


def generate_map_view(df, slug, dataset_map=None):
    import json
    from branca.element import Element

    if slug not in dataset_map:
        return html.P("Non-valid dataset")

    result = get_data(dataset_map[slug], df["url_reference"])
    df_data = result["data"].dropna(subset=["latitude", "longitude"]).copy()

    m = folium.Map(
        location=[df_data["latitude"].mean(), df_data["longitude"].mean()],
        zoom_start=5
    )

    # IMPORTANT: load libs inside the iframe using YOUR asset filenames
    m.get_root().header.add_child(Element('<link rel="stylesheet" href="/dash/assets/10_leaflet.css">'))
    m.get_root().header.add_child(Element('<link rel="stylesheet" href="/dash/assets/20_leaflet.draw.css">'))
    m.get_root().header.add_child(Element('<script src="/dash/assets/10_leaflet.js"></script>'))
    m.get_root().header.add_child(Element('<script src="/dash/assets/20_leaflet.draw.js"></script>'))
    m.get_root().header.add_child(Element('<script src="/dash/assets/30_turf.min.js"></script>'))

    # Draw tools
    Draw(
        export=False,
        draw_options={
            "polyline": False,
            "rectangle": True,
            "polygon": True,
            "circle": False,
            "marker": False,
            "circlemarker": False
        },
        edit_options={"edit": True, "remove": True}
    ).add_to(m)

    # Visible points
    marker_cluster = MarkerCluster().add_to(m)
    for _, row in df_data.iterrows():
        folium.CircleMarker(
            location=[float(row["latitude"]), float(row["longitude"])],
            radius=3,
            tooltip=str(row.get("site_name", "")),
            fill=True,
            fill_opacity=0.7
        ).add_to(marker_cluster)

    # Points for JS selection
    js_points = []
    for _, row in df_data.iterrows():
        js_points.append({
            "site_name": row.get("site_name", ""),
            "sample_name": row.get("sample_name", ""),
            "dataset": slug,
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"])
        })

    points_json = json.dumps(js_points)
    map_name = m.get_name()

    # NOTE: NO <script> tag here – we inject into folium's script section
    export_js = f"""
    console.log("EXPORT SCRIPT LOADED");

    (function() {{

    function escapeCsv(v) {{
        if (v === null || v === undefined) return "";
        var s = String(v);
        if (s.includes('"') || s.includes(',') || s.includes('\\n')) {{
        s = '"' + s.replace(/"/g, '""') + '"';
        }}
        return s;
    }}

    function downloadCSV(rows) {{
        var header = ["site_name","sample_name","latitude","longitude","dataset"];
        var out = [header.join(",")];

        rows.forEach(function(p) {{
        out.push([
            escapeCsv(p.site_name),
            escapeCsv(p.sample_name),
            escapeCsv(p.latitude),
            escapeCsv(p.longitude),
            escapeCsv(p.dataset)
        ].join(","));
        }});

        var csv = out.join("\\n");
        var blob = new Blob([csv], {{type: "text/csv;charset=utf-8;"}});
        var url = URL.createObjectURL(blob);

        var a = document.createElement("a");
        a.href = url;
        a.download = "selected_points.csv";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }}

    function ensureButton(map) {{
        var container = map.getContainer();
        if (container.querySelector("#download-selection-btn")) return;

        container.style.position = "relative";

        var btn = document.createElement("button");
        btn.id = "download-selection-btn";
        btn.type = "button";
        btn.textContent = "⬇ Download selection";
        btn.style.position = "absolute";
        btn.style.top = "10px";
        btn.style.left = "10px";
        btn.style.zIndex = "999999";
        btn.style.padding = "6px 10px";
        btn.style.border = "1px solid #999";
        btn.style.borderRadius = "4px";
        btn.style.background = "white";
        btn.style.cursor = "pointer";

        btn.addEventListener("click", function(e) {{
        e.preventDefault();
        e.stopPropagation();

        if (!window.__selectedPoints || window.__selectedPoints.length === 0) {{
            alert("No selection yet. Draw a rectangle/polygon first.");
            return;
        }}
        downloadCSV(window.__selectedPoints);
        }});

        container.appendChild(btn);
    }}

    var tries = 0;
    var t = setInterval(function() {{
        tries++;

        var mapOk = (typeof {map_name} !== "undefined");
        var leafletOk = (typeof L !== "undefined");
        var drawOk = leafletOk && !!L.Draw;
        var turfOk = (typeof turf !== "undefined");

        if (mapOk && leafletOk) {{
        var map = {map_name};
        ensureButton(map);

        // Only enable selection when draw+turf exist
        if (drawOk && turfOk) {{
            clearInterval(t);

            var POINTS = {points_json};
            window.__selectedPoints = [];

            var drawnItems = window.__drawnItems || new L.FeatureGroup();
            if (!window.__drawnItems) {{
            map.addLayer(drawnItems);
            window.__drawnItems = drawnItems;
            }}

            map.off(L.Draw.Event.CREATED);
            map.on(L.Draw.Event.CREATED, function(e) {{
            drawnItems.clearLayers();
            drawnItems.addLayer(e.layer);

            var shape = e.layer.toGeoJSON();
            var selected = [];

            for (var i = 0; i < POINTS.length; i++) {{
                var p = POINTS[i];
                var pt = turf.point([p.longitude, p.latitude]);
                if (turf.booleanPointInPolygon(pt, shape)) {{
                selected.push(p);
                }}
            }}

            window.__selectedPoints = selected;

            var btn = map.getContainer().querySelector("#download-selection-btn");
            if (btn) btn.textContent = "⬇ Download selection (" + selected.length + ")";
            }});

            return;
        }}
        }}

        if (tries > 200) {{
        clearInterval(t);
        console.error("Export init failed:", {{
            mapOk: mapOk, leafletOk: leafletOk, drawOk: drawOk, turfOk: turfOk
        }});
        }}
    }}, 50);

    }})();
    """

    # ✅ Correct injection point for JS
    m.get_root().script.add_child(Element(export_js))

    return html.Iframe(
        srcDoc=m.get_root().render(),
        style={"width": "100%", "height": "100%", "border": "none", "flex": "1"}
    )

def generate_all_datasets_map(df=None, dataset_map=None, dataset_slugs=None, coloramp='tab20b'):
    """
    Generate a map of all available datasets
    
    :param df: Description
    :param dataset_map: Description
    :param dataset_slugs: Description
    :param coloramp: Description
    :return: Description
    :rtype: Iframe
    """
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    # import pandas as pd
    from shapely.geometry import MultiPoint
    import geopandas as gpd
    import folium
    # from IPython.display import HTML
    # import html

    all_points = []  # To collect all lat/lon for mean center calculation

    # === First pass: Collect all points ===
    for slug in dataset_slugs:
        try:
            result = get_data(dataset_map[slug], df["url_reference"])
            df_data = result['data']
            df_data = df_data.dropna(subset=['latitude', 'longitude'])
            all_points.extend(zip(df_data['latitude'], df_data['longitude']))
        except Exception as e:
            print(f"Failed to load dataset {slug} for center calculation: {e}")

    # === Compute mean center from all collected lat/lon ===
    if all_points:
        latitudes, longitudes = zip(*all_points)
        mean_lat = sum(latitudes) / len(latitudes)
        mean_lon = sum(longitudes) / len(longitudes)
    else:
        mean_lat, mean_lon = 45, 5  # fallback default center

    # === Initialize the map using calculated center ===
    m = folium.Map(location=[mean_lat, mean_lon], zoom_start=5)
    
    # === Color mapping ===
    cmap = plt.get_cmap(coloramp)
    colors = [mcolors.to_hex(cmap(i / len(dataset_slugs))) for i in range(len(dataset_slugs))]

    # === Plot data ===
    for idx, slug in enumerate(dataset_slugs):
        try:
            result = get_data(dataset_map[slug], df["url_reference"])
            df_data = result['data']
            df_data = df_data.dropna(subset=['latitude', 'longitude'])

            points = list(zip(df_data['longitude'], df_data['latitude']))
            if len(points) >= 3:
                multipoint = MultiPoint(points)
                hull = multipoint.convex_hull
                geojson = gpd.GeoSeries([hull]).__geo_interface__
                folium.GeoJson(
                    geojson,
                    name=slug,
                    style_function=lambda x, color=colors[idx % len(colors)]: {
                        'fillColor': color, 'color': color, 'weight': 2, 'fillOpacity': 0.3
                    },
                    tooltip=slug,
                    popup=folium.Popup(
                        f"<a href='/dash/mapview?dataset={slug}' target='_blank'>{slug}</a>")
                ).add_to(m)
                

            for _, row in df_data.iterrows():
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=2,
                    color=colors[idx % len(colors)],
                    fill=True,
                    fill_opacity=0.7,
                    tooltip=row.get('site_name', slug)
                ).add_to(m)
        except Exception as e:
            print(f"Failed to load dataset {slug}: {e}")
            
    # Draw tools (now safe because Dash assets/ load Leaflet first (dashboard\assets\10_leaflet.js))
    Draw(
        export=False,
        draw_options={
            "polyline": False,
            "rectangle": True,
            "polygon": True,
            "circle": False,
            "marker": False,
            "circlemarker": False
        },
        edit_options={"edit": True, "remove": True}
    ).add_to(m)

    return html.Iframe(srcDoc=m.get_root().render(), width='100%', height='100%')
