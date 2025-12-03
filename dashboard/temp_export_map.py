import folium
import pandas as pd
import json

# ----------------------------------------------------
# 1. Load your dataset (TSV or CSV)
# ----------------------------------------------------
df = pd.read_csv(
    "https://raw.githubusercontent.com/iramat/almacir/refs/heads/hugo-files/static/sites.tsv",
    sep=r"\s+",
    engine="python"
)

# Drop rows without coordinates
df = df.dropna(subset=["lat", "lon"])

# ----------------------------------------------------
# 2. Convert dataset to GeoJSON (for JS processing)
# ----------------------------------------------------
features = []
for _, row in df.iterrows():
    features.append({
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [float(row["lon"]), float(row["lat"])]
        },
        "properties": {
            "name": row["name_fr"],
            "type": row["type"]
        }
    })

geojson_data = {"type": "FeatureCollection", "features": features}

# ----------------------------------------------------
# 3. Create Folium map
# ----------------------------------------------------
m = folium.Map(
    location=[df["lat"].mean(), df["lon"].mean()],
    zoom_start=5
)

# Add the sites layer
geojson_layer = folium.GeoJson(
    geojson_data,
    name="Sites",
    marker=folium.CircleMarker(radius=5, color="red", fill=True)
)
geojson_layer.add_to(m)

# ----------------------------------------------------
# 4. Add drawing tools
# ----------------------------------------------------
draw = folium.plugins.Draw(
    export=False,
    draw_options={
        "polyline": False,
        "polygon": False,
        "circle": False,
        "circlemarker": False,
        "marker": False,
        "rectangle": True
    },
    edit_options={"edit": False}
)
draw.add_to(m)

# # ----------------------------------------------------
# # 5. Add custom JS: rectangle selection + CSV export
# # ----------------------------------------------------
# template = f"""
# <script>

# // Load Turf.js
# var turfScript = document.createElement('script');
# turfScript.src = 'https://cdn.jsdelivr.net/npm/@turf/turf@6/turf.min.js';
# document.head.appendChild(turfScript);

# var geojsonData = {json.dumps(geojson_data)};

# // When rectangle is created
# map.on('draw:created', function (e) {{
#     var layer = e.layer;
#     var bounds = layer.getBounds();

#     // Convert rectangle bounds to polygon
#     var poly = turf.bboxPolygon([
#         bounds.getWest(), bounds.getSouth(),
#         bounds.getEast(), bounds.getNorth()
#     ]);

#     // Collect selected points
#     var selected = [];
#     geojsonData.features.forEach(function (feat) {{
#         var pt = turf.point(feat.geometry.coordinates);
#         if (turf.booleanPointInPolygon(pt, poly)) {{
#             selected.push(feat.properties);
#         }}
#     }});

#     if (selected.length === 0) {{
#         alert("No sites selected.");
#         return;
#     }}

#     // Convert to CSV
#     var csv = "name,type\\n";
#     selected.forEach(function(row) {{
#         csv += row.name + "," + row.type + "\\n";
#     }});

#     // Download CSV
#     var blob = new Blob([csv], {{ type: "text/csv;charset=utf-8;" }});
#     var url = URL.createObjectURL(blob);
#     var a = document.createElement("a");
#     a.href = url;
#     a.download = "selected_sites.csv";
#     document.body.appendChild(a);
#     a.click();
#     document.body.removeChild(a);
# }});

# </script>
# """

m.get_root().html.add_child(folium.Element(template))

# ----------------------------------------------------
# 6. Save map
# ----------------------------------------------------
# m.save("selection_map.html")
# print("Map saved → selection_map.html")
