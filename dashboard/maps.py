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
    Map for all datasets (landing map)
    
    :param df: Description
    :param dataset_map: Description
    :param dataset_slugs: Description
    :param coloramp: Description
    """
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
    from shapely.geometry import MultiPoint
    import geopandas as gpd
    import folium
    import pandas as pd

    # --- Collect all points for centering and for JS selection ---
    all_points_latlon = []
    all_points_records = []  # records for JS selection/export

    for slug in dataset_slugs:
        try:
            result = get_data(dataset_map[slug], df["url_reference"])
            df_data = result["data"].dropna(subset=["latitude", "longitude"]).copy()

            # collect for map center
            all_points_latlon.extend(zip(df_data["latitude"], df_data["longitude"]))

            # collect for JS selection/export
            # for _, row in df_data.iterrows():
            #     all_points_records.append({
            #         "site_name": row.get("site_name", ""),
            #         "sample_name": row.get("sample_name", ""),
            #         "dataset": slug,
            #         "latitude": float(row["latitude"]),
            #         "longitude": float(row["longitude"])
            #     })
            # Create a copy and add the slug column
            
            # Assuming 'slug' comes from your outer loop
            for _, row in df_data.iterrows():
                # 1. Create the base record from all columns in the row
                record = row.to_dict()
                
                # 2. Add or update specific fields
                # We use .update() or direct assignment to ensure specific logic is applied
                record.update({
                    "dataset": slug,
                    "latitude": float(row["latitude"]),
                    "longitude": float(row["longitude"])
                })
                
                # 3. Append to the master list
                all_points_records.append(record)
            
        except Exception as e:
            print(f"Failed to load dataset {slug} for points collection: {e}")
            
    # print(df_data.columns) # OK

    # --- Compute map center ---
    if all_points_latlon:
        latitudes, longitudes = zip(*all_points_latlon)
        mean_lat = sum(latitudes) / len(latitudes)
        mean_lon = sum(longitudes) / len(longitudes)
    else:
        mean_lat, mean_lon = 45, 5

    # --- Initialize map ---
    m = folium.Map(location=[mean_lat, mean_lon], zoom_start=5)

    # --- IMPORTANT: load your libs INSIDE the iframe (match your assets filenames) ---
    # If your Leaflet/Draw/Turf are not in assets with these names, change them here.
    m.get_root().header.add_child(Element('<link rel="stylesheet" href="/dash/assets/10_leaflet.css">'))
    m.get_root().header.add_child(Element('<link rel="stylesheet" href="/dash/assets/20_leaflet.draw.css">'))
    m.get_root().header.add_child(Element('<script src="/dash/assets/10_leaflet.js"></script>'))
    m.get_root().header.add_child(Element('<script src="/dash/assets/20_leaflet.draw.js"></script>'))
    m.get_root().header.add_child(Element('<script src="/dash/assets/30_turf.min.js"></script>'))

    # --- Add draw tools (rectangle + polygon) ---
    Draw(
        export=False,
        draw_options={
            "polyline": False,
            "rectangle": True,
            "polygon": True,
            "circle": False,
            "marker": False,
            "circlemarker": False,
        },
        edit_options={"edit": True, "remove": True},
    ).add_to(m)

    # --- Color mapping for datasets ---
    cmap = plt.get_cmap(coloramp)
    colors = [mcolors.to_hex(cmap(i / max(1, len(dataset_slugs)))) for i in range(len(dataset_slugs))]

    # --- Plot hulls + circle points ---
    for idx, slug in enumerate(dataset_slugs):
        try:
            result = get_data(dataset_map[slug], df["url_reference"])
            df_data = result["data"].dropna(subset=["latitude", "longitude"]).copy()
            
            # hull
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

            # points
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

    # --- Inject selection + download button JS into Folium's script section ---
    map_name = m.get_name()
    # def _json_safe(v):
    #     # Convert pandas/numpy stuff to JSON-safe primitives
    #     if pd.isna(v):
    #         return None
    #     # convert timestamps/dates to strings
    #     try:
    #         import pandas as pd
    #         if isinstance(v, pd.Timestamp):
    #             return v.isoformat()
    #     except Exception:
    #         pass
    #     return v

    # # make every record JSON-safe
    # safe_records = []
    # for rec in all_points_records:
    #     safe_records.append({k: _json_safe(v) for k, v in rec.items()})

    # points_json = json.dumps(safe_records, ensure_ascii=False)
    
    points_json = json.dumps(all_points_records)

    export_js = f"""
console.log("OVERVIEW EXPORT SCRIPT LOADED");

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
    if (rows.length === 0) return;

    // 1. Dynamically get all keys (column names) from the first object
    var header = Object.keys(rows[0]);
    
    // 2. Create the header row
    var out = [header.join(",")];

    // 3. Iterate through each selected point
    rows.forEach(function(p) {{
      var row = header.map(function(fieldName) {{
        // Look up the value for this specific column name
        return escapeCsv(p[fieldName]);
    }});
      out.push(row.join(","));
    }});

    // 4. Trigger the download
    var csv = out.join("\\n");
    var blob = new Blob([csv], {{type: "text/csv;charset=utf-8;"}});
    var url = URL.createObjectURL(blob);
    
    // Build filename: chips_YYYY-MM-DD_<N>.csv
    var today = new Date();
    var yyyy = today.getFullYear();
    var mm = String(today.getMonth() + 1).padStart(2, "0");
    var dd = String(today.getDate()).padStart(2, "0");

    var dateStr = yyyy + "-" + mm + "-" + dd;
    var count = rows.length;

    var a = document.createElement("a");
    a.href = url;
    // a.download = "selected_points.csv";
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
  
  

  // Wait for map + Leaflet at minimum, show button immediately
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

      // enable selection when draw+turf are ready
      if (drawOk && turfOk) {{
        clearInterval(t);

        var POINTS = {points_json};
        window.__selectedPoints = [];

        var drawnItems = new L.FeatureGroup();
        map.addLayer(drawnItems);

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
      console.error("Overview export init failed:", {{
        mapOk: mapOk, leafletOk: leafletOk, drawOk: drawOk, turfOk: turfOk
      }});
    }}
  }}, 50);

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



