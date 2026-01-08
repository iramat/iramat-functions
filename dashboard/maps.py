import geopandas as gpd
# import html
from dash import html
import folium
from folium.plugins import MarkerCluster, Draw
from shapely.geometry import MultiPoint
import json
from branca.element import Element
from get_data import get_data

def generate_all_datasets_map(df=None, dataset_map=None, dataset_slugs=None, coloramp="tab20b"):
    """
    Landing map with: hulls + points + draw selection (rectangle/polygon) + delete + download CSV button.
    """
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    from shapely.geometry import MultiPoint
    import geopandas as gpd
    import folium
    import pandas as pd
    import json
    from branca.element import Element

    # --- Collect all points for centering and for JS selection ---
    all_points_latlon = []
    all_points_records = []

    for slug in dataset_slugs:
        try:
            result = get_data(dataset_map[slug], df["url_reference"])
            df_data = result["data"].dropna(subset=["latitude", "longitude"]).copy()

            all_points_latlon.extend(zip(df_data["latitude"], df_data["longitude"]))

            for _, row in df_data.iterrows():
                rec = row.to_dict()

                # make JSON-safe-ish (timestamps / NaN)
                for k, v in list(rec.items()):
                    if pd.isna(v):
                        rec[k] = None
                    elif isinstance(v, pd.Timestamp):
                        rec[k] = v.isoformat()

                # ensure required fields exist and are numbers
                rec["dataset"] = slug
                rec["latitude"] = float(row["latitude"])
                rec["longitude"] = float(row["longitude"])

                all_points_records.append(rec)

        except Exception as e:
            print(f"Failed to load dataset {slug} for points collection: {e}")

    # --- Compute map center ---
    if all_points_latlon:
        latitudes, longitudes = zip(*all_points_latlon)
        mean_lat = sum(latitudes) / len(latitudes)
        mean_lon = sum(longitudes) / len(longitudes)
    else:
        mean_lat, mean_lon = 45, 5

    # --- Initialize map ---
    m = folium.Map(location=[mean_lat, mean_lon], zoom_start=5)

    # --- Color mapping ---
    cmap = plt.get_cmap(coloramp)
    colors = [mcolors.to_hex(cmap(i / max(1, len(dataset_slugs)))) for i in range(len(dataset_slugs))]

    # --- Plot hulls + points ---
    for idx, slug in enumerate(dataset_slugs):
        try:
            result = get_data(dataset_map[slug], df["url_reference"])
            df_data = result["data"].dropna(subset=["latitude", "longitude"]).copy()

            points = list(zip(df_data["longitude"], df_data["latitude"]))
            if len(points) >= 3:
                hull = MultiPoint(points).convex_hull
                geojson = gpd.GeoSeries([hull]).__geo_interface__
                folium.GeoJson(
                    geojson,
                    name=slug,
                    style_function=lambda x, color=colors[idx % len(colors)]: {
                        "fillColor": color,
                        "color": color,
                        "weight": 2,
                        "fillOpacity": 0.3,
                    },
                    tooltip=slug,
                    popup=folium.Popup(f"<a href='/dash/mapview?dataset={slug}' target='_blank'>{slug}</a>"),
                ).add_to(m)

            for _, row in df_data.iterrows():
                folium.CircleMarker(
                    location=[float(row["latitude"]), float(row["longitude"])],
                    radius=2,
                    color=colors[idx % len(colors)],
                    fill=True,
                    fill_opacity=0.7,
                    tooltip=row.get("site_name", slug),
                ).add_to(m)

        except Exception as e:
            print(f"Failed to load dataset {slug}: {e}")

    map_name = m.get_name()
    points_json = json.dumps(all_points_records, ensure_ascii=False)

    # --- Inject everything via one loader that guarantees order inside srcdoc ---
    export_js = f"""
console.log("OVERVIEW EXPORT SCRIPT LOADED");

(function() {{
  // ---- tiny loader to ensure order: Leaflet (from Folium) -> Leaflet.draw -> turf ----
  function loadScript(src) {{
    return new Promise(function(resolve, reject) {{
      var s = document.createElement("script");
      s.src = src;
      s.onload = resolve;
      s.onerror = function() {{ reject(new Error("Failed to load " + src)); }};
      document.head.appendChild(s);
    }});
  }}

  function loadCss(href) {{
    return new Promise(function(resolve, reject) {{
      var l = document.createElement("link");
      l.rel = "stylesheet";
      l.href = href;
      l.onload = resolve;
      l.onerror = function() {{ reject(new Error("Failed to load " + href)); }};
      document.head.appendChild(l);
    }});
  }}
 
  function escapeCsv(v) {{
    if (v === null || v === undefined) return "";
    var s = String(v);
    if (s.includes('"') || s.includes(',') || s.includes('\\n')) {{
      s = '"' + s.replace(/"/g, '""') + '"';
    }}
    return s;
  }}


  function downloadCSV(rows) {{
    if (!rows || rows.length === 0) return;

    // union of keys (all columns)
    var headerSet = {{}};
    rows.forEach(function(r) {{
      Object.keys(r || {{}}).forEach(function(k) {{ headerSet[k] = true; }});
    }});
    var header = Object.keys(headerSet);

    var out = [header.join(",")];
    rows.forEach(function(p) {{
      var row = header.map(function(fieldName) {{
        return escapeCsv(p ? p[fieldName] : "");
      }});
      out.push(row.join(","));
    }});

    var csv = out.join("\\r\\n");

    var blob = new Blob([csv], {{type: "text/csv;charset=utf-8;"}});
    var url = URL.createObjectURL(blob);

    // chips_dYYYY-MM-DD_nN.csv
    var today = new Date();
    var yyyy = today.getFullYear();
    var mm = String(today.getMonth() + 1).padStart(2, "0");
    var dd = String(today.getDate()).padStart(2, "0");
    var dateStr = yyyy + "-" + mm + "-" + dd;
    var count = rows.length;

    var a = document.createElement("a");
    a.href = url;
    a.download = "chips_d" + dateStr + "_n" + count + ".csv";
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
    btn.textContent = "Download selection";
    btn.style.position = "absolute";
    btn.style.top = "10px";
    btn.style.left = "50px";
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

  // wait for Folium to create the map + Leaflet global L
  function waitForLeafletAndMap() {{
    return new Promise(function(resolve, reject) {{
      var tries = 0;
      var t = setInterval(function() {{
        tries++;
        var mapOk = (typeof {map_name} !== "undefined");
        var leafletOk = (typeof L !== "undefined");

        if (mapOk && leafletOk) {{
          clearInterval(t);
          resolve({map_name});
        }}
        if (tries > 200) {{
          clearInterval(t);
          reject(new Error("Map/Leaflet not ready"));
        }}
      }}, 50);
    }});
  }}

  waitForLeafletAndMap()
    .then(function(map) {{
      ensureButton(map);

      // IMPORTANT: load draw + turf only after Leaflet exists
      return Promise.all([
        loadCss("/dash/assets/20_leaflet.draw.css"),
        loadScript("/dash/assets/20_leaflet.draw.js"),
        loadScript("/dash/assets/30_turf.min.js"),
      ]).then(function() {{ return map; }});
    }})
    .then(function(map) {{
      if (!L.Control || !L.Control.Draw) {{
        console.error("Leaflet.draw did not attach (L.Control.Draw missing).");
        return;
      }}

      var POINTS = {points_json};
      window.__selectedPoints = [];

      // One editable group wired to toolbar => delete works
      var editableLayers = new L.FeatureGroup();
      map.addLayer(editableLayers);

      var drawControl = new L.Control.Draw({{
        edit: {{ featureGroup: editableLayers, remove: true }},
        draw: {{
          polyline: false,
          rectangle: true,
          polygon: true,
          circle: false,
          marker: false,
          circlemarker: false
        }}
      }});
      map.addControl(drawControl);

      map.on(L.Draw.Event.CREATED, function(e) {{
        editableLayers.clearLayers();
        editableLayers.addLayer(e.layer);

        if (typeof turf === "undefined") {{
          alert("Turf is not loaded, selection export is disabled.");
          window.__selectedPoints = [];
          return;
        }}

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

      map.on("draw:deleted", function() {{
        window.__selectedPoints = [];
        var btn = map.getContainer().querySelector("#download-selection-btn");
        if (btn) btn.textContent = "Download selection";
      }});
    }})
    .catch(function(err) {{
      console.error(err);
    }});

}})();
"""
    m.get_root().script.add_child(Element(export_js))

    return html.Iframe(srcDoc=m.get_root().render(), width="100%", height="100%")

def generate_map_view(df, slug, dataset_map = None, ):
    """
    Map for a specific dataset
    
    :param df: Description
    :param slug: Description
    :param dataset_map: Description
    """
    if slug not in dataset_map:
        return html.P("Jeu de données invalide.")

    result = get_data(dataset_map[slug], df["url_reference"])
    df_data = result['data']
    df_data = df_data.dropna(subset=['latitude', 'longitude'])
    
    df_data['dataset_name'] = slug

    m = folium.Map(location=[df_data['latitude'].mean(), df_data['longitude'].mean()], zoom_start=5)
    marker_cluster = MarkerCluster().add_to(m)

    for name, group in df_data.groupby('dataset_name'):
        points = list(zip(group['longitude'], group['latitude']))
        if len(points) >= 3:
            multipoint = MultiPoint(points)
            hull = multipoint.convex_hull
            geojson = gpd.GeoSeries([hull]).__geo_interface__
            folium.GeoJson(geojson, name=name, tooltip=name).add_to(m)
        for _, row in group.iterrows():
            folium.Marker(
                location=[row['latitude'], row['longitude']],
                tooltip=row['site_name']
            ).add_to(marker_cluster)

    map_html = m.get_root().render()
    # return html.Iframe(srcDoc=map_html, width='100%', height='100%')
    # return html.Iframe(
    #     srcDoc=map_html,
    #     style={"width": "100%", "height": "100vh", "border": "none"}
    # )
    return html.Iframe(
        srcDoc=map_html,
        style={"width": "100%", "height": "100%", "border": "none", "flex": "1"}
    )



# def generate_all_datasets_map(df = None, dataset_map = None, dataset_slugs = None, coloramp = 'tab20b'):
    
#     import matplotlib.pyplot as plt
#     import matplotlib.colors as mcolors
    
#     m = folium.Map(location=[45, 5], zoom_start=5)
    
#     cmap = plt.get_cmap(coloramp)  # previously: 'hsv'. Good hue variety for many categories
#     colors = [mcolors.to_hex(cmap(i / len(dataset_slugs))) for i in range(len(dataset_slugs))]
    
#     for idx, slug in enumerate(dataset_slugs):
#         try:
#             result = get_data(dataset_map[slug], df["url_reference"])
#             df_data = result['data']
#             df_data = df_data.dropna(subset=['latitude', 'longitude'])

#             points = list(zip(df_data['longitude'], df_data['latitude']))
#             if len(points) >= 3:
#                 # print(colors[idx % len(colors)])
#                 multipoint = MultiPoint(points)
#                 hull = multipoint.convex_hull
#                 geojson = gpd.GeoSeries([hull]).__geo_interface__
#                 folium.GeoJson(
#                     geojson,
#                     name=slug,
#                     style_function=lambda x, color=colors[idx % len(colors)]: {
#                         'fillColor': color, 'color': color, 'weight': 2, 'fillOpacity': 0.3
#                     },
#                     tooltip=slug,
#                     popup=folium.Popup(f"<a href='/dash/mapview?dataset={slug}' target='_blank'>{slug}</a>")
#                 ).add_to(m)

#             for _, row in df_data.iterrows():
#                 folium.CircleMarker(
#                     location=[row['latitude'], row['longitude']],
#                     radius=2,
#                     color=colors[idx % len(colors)],
#                     fill=True,
#                     fill_opacity=0.7,
#                     tooltip=row['site_name']
#                 ).add_to(m)
#         except Exception as e:
#             print(f"Failed to load dataset {slug}: {e}")

#     return html.Iframe(srcDoc=m.get_root().render(), width='100%', height='100%')



