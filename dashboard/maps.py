import geopandas as gpd
# import html
from dash import html
import folium
from folium.plugins import MarkerCluster
from shapely.geometry import MultiPoint
from get_data import get_data


def generate_map_view(df, slug, dataset_map = None, ):
    
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
    return html.Iframe(srcDoc=map_html, width='100%', height='600')

def generate_all_datasets_map(dataset_map = None, dataset_slugs = None):
    m = folium.Map(location=[45, 5], zoom_start=5)
    
    colors = [
    'red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightblue',
    'darkblue', 'lightgreen', 'cadetblue', 'darkgreen', 'lightred',
    'black', 'gray', 'pink', 'lightgray', 'beige', 'brown', 'darkpurple',
    'lightgray', 'yellow', 'lightyellow', 'navy', 'teal', 'aqua', 'gold',
    'coral']
    
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
                    popup=folium.Popup(f"<a href='/dash/mapview?dataset={slug}' target='_blank'>{slug}</a>")
                ).add_to(m)

            for _, row in df_data.iterrows():
                folium.CircleMarker(
                    location=[row['latitude'], row['longitude']],
                    radius=3,
                    color=colors[idx % len(colors)],
                    fill=True,
                    fill_opacity=0.7,
                    tooltip=row['site_name']
                ).add_to(m)
        except Exception as e:
            print(f"Failed to load dataset {slug}: {e}")

    return html.Iframe(srcDoc=m.get_root().render(), width='100%', height='700')