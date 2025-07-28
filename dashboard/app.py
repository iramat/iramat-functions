# Bulk upload of the dash functions
# in the VM:
#   - run './_upload_from_gh.sh' to upload the updated functions from GitHub. 
#   - after what, remember to update the app.py with the appropriate app name:
#   """
#   app = dash.Dash(
#     __name__,
#     requests_pathname_prefix='/dash/',
#     routes_pathname_prefix='/dash/'
#   )
#   """
#   - set `web = False`

import os
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import re
# import pandas as pd
import folium
from folium.plugins import MarkerCluster
from shapely.geometry import MultiPoint
import geopandas as gpd
from get_data import get_data
from urls import read_data_urls
from maps import generate_map_view
from maps import generate_all_datasets_map


# assets_path = os.path.join(os.path.dirname(__file__), 'assets')

# web = False
# local = not web

tit = "CHIPS Dashboard"

df = read_data_urls(read_ref=False)
dataset_slugs = df['dataset_name']
dataset_map = dict(zip(dataset_slugs, df['url_data']))

# # Initialize app
app = dash.Dash(
    __name__,
    # assets_folder=assets_path,
    requests_pathname_prefix='/dash/',
    routes_pathname_prefix='/dash/',
    suppress_callback_exceptions=True
)

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        <link rel="icon" type="image/png" href="/dash/assets/logo.png">
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.title = tit
# app.favicon = ("logo.ico")
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# def generate_map_view(slug):
#     if slug not in dataset_map:
#         return html.P("Jeu de données invalide.")

#     result = get_data(dataset_map[slug], df["url_reference"])
#     df_data = result['data']
#     df_data = df_data.dropna(subset=['latitude', 'longitude'])
    
#     df_data['dataset_name'] = slug

#     m = folium.Map(location=[df_data['latitude'].mean(), df_data['longitude'].mean()], zoom_start=5)
#     marker_cluster = MarkerCluster().add_to(m)

#     for name, group in df_data.groupby('dataset_name'):
#         points = list(zip(group['longitude'], group['latitude']))
#         if len(points) >= 3:
#             multipoint = MultiPoint(points)
#             hull = multipoint.convex_hull
#             geojson = gpd.GeoSeries([hull]).__geo_interface__
#             folium.GeoJson(geojson, name=name, tooltip=name).add_to(m)
#         for _, row in group.iterrows():
#             folium.Marker(
#                 location=[row['latitude'], row['longitude']],
#                 tooltip=row['site_name']
#             ).add_to(marker_cluster)

#     map_html = m.get_root().render()
#     return html.Iframe(srcDoc=map_html, width='100%', height='600')

# def generate_all_datasets_map():
#     m = folium.Map(location=[45, 5], zoom_start=5)
    
#     colors = [
#     'red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightblue',
#     'darkblue', 'lightgreen', 'cadetblue', 'darkgreen', 'lightred',
#     'black', 'gray', 'pink', 'lightgray', 'beige', 'brown', 'darkpurple',
#     'lightgray', 'yellow', 'lightyellow', 'navy', 'teal', 'aqua', 'gold',
#     'coral']
    
#     for idx, slug in enumerate(dataset_slugs):
#         try:
#             result = get_data(dataset_map[slug], df["url_reference"])
#             df_data = result['data']
#             df_data = df_data.dropna(subset=['latitude', 'longitude'])

#             points = list(zip(df_data['longitude'], df_data['latitude']))
#             if len(points) >= 3:
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
#                     radius=3,
#                     color=colors[idx % len(colors)],
#                     fill=True,
#                     fill_opacity=0.7,
#                     tooltip=row['site_name']
#                 ).add_to(m)
#         except Exception as e:
#             print(f"Failed to load dataset {slug}: {e}")

#     return html.Iframe(srcDoc=m.get_root().render(), width='100%', height='700')


@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname'),
    State('url', 'search')
)
def display_page(pathname, search):
    # Remove '/dash/' prefix to isolate the slug
    path = pathname.replace('/dash/', '').strip('/')

    if path == "" or path == "index":
        return html.Div(style={'display': 'flex'}, children=[
                html.Div(style={'width': '250px', 'padding': '20px', 'backgroundColor': '#f2f2f2'}, children=[
                html.H2("Welcome"),
                html.P([
                        "This dashboard helps exploring the CHIPS database. See also: ",
                        html.A("GitHub", 
                               href="https://github.com/iramat/iramat-dev/tree/main/dbs/chips",
                               target="_blank")
                    ]),
                html.H3("Datasets"),
                html.Ul([
                    html.Li(html.A(slug, href=f"/dash/mapview?dataset={slug}")) for slug in dataset_slugs
                ])
            ]),
            html.Div(style={'flex': '1', 'padding': '20px'}, children=[
                generate_all_datasets_map(dataset_map = dataset_map, dataset_slugs = dataset_slugs)
            ])
        ])

    if path == "mapview" and search:
        slug = search.split('=')[-1]
        return html.Div(style={'display': 'flex'}, children=[
            html.Div(style={'width': '200px', 'padding': '20px', 'backgroundColor': '#f2f2f2'}, children=[
                html.H2("Dataset List"),
                html.Ul([
                    html.Li(html.A("🏠 Back to Home", href="/dash/")),
                    html.Li(html.A("📈 View Line Chart", href=f"/dash/{slug}")),
                    html.Hr(),
                    *[
                        html.Li(html.A(s, href=f"/dash/mapview?dataset={s}"))
                        for s in dataset_slugs
                    ]
                ])
            ]),
            html.Div(style={'flex': '1', 'padding': '20px'}, children=[
                generate_map_view(df, slug, dataset_map)
            ])
        ])


    if path == "dataset" and search:
        slug = search.split('=')[-1]
        return html.Div(style={'display': 'flex'}, children=[
            html.Div(style={'width': '200px', 'padding': '20px', 'backgroundColor': '#f2f2f2'}, children=[
                html.H1(tit),
                html.H2("Dataset List"),
                html.Ul([
                    html.Li(html.A("🏠 Back to Home", href="/dash/")),
                    html.Li(html.A("🗺️ View Map", href=f"/dash/mapview?dataset={slug}")),
                    html.Hr(),
                    *[
                        html.Li(html.A(s, href=f"/dash/{s}")) for s in dataset_slugs
                    ]
                ])
            ]),
            html.Div(style={'flex': '1', 'padding': '20px'}, children=[
                generate_dataset_page(dataset_map[slug])
            ])
        ])
        # slug = search.split('=')[-1]
        # return html.Div(style={'display': 'flex'}, children=[
        #     html.Div(style={'width': '250px', 'padding': '20px', 'backgroundColor': '#f2f2f2'}, children=[
        #         html.H2("Dataset List (Map View)"),
        #         html.Ul([
        #             html.Li(html.A("🏠 Back to Home", href="/dash/")),
        #             html.Li(html.A("📈 View Line Chart", href=f"/dash/{slug}")),
        #             html.Hr(),
        #             *[
        #                 html.Li(html.A(s, href=f"/dash/mapview?dataset={s}"))
        #                 for s in dataset_slugs
        #             ]
        #         ])
        #     ]),
        #     html.Div(style={'flex': '1', 'padding': '20px'}, children=[
        #         generate_map_view(slug)
        #     ])
        # ])

    # elif path in dataset_map:
    #     slug = path
    #     return html.Div(style={'display': 'flex'}, children=[
    #         html.Div(style={'width': '250px', 'padding': '20px', 'backgroundColor': '#f2f2f2'}, children=[
    #             html.H2("Dataset Navigation"),
    #             html.Ul([
    #                 html.Li(html.A("🏠 Back to Home", href="/dash/")),
    #                 html.Li(html.A("🗺️ View Map", href=f"/dash/mapview?dataset={slug}")),
    #                 html.Hr(),
    #                 *[
    #                     html.Li(html.A(s, href=f"/dash/{s}")) for s in dataset_slugs
    #                 ]
    #             ])
    #         ]),
    #         html.Div(style={'flex': '1', 'padding': '20px'}, children=[
    #             generate_dataset_page(dataset_map[slug])
    #         ])
    #     ])
 

    elif path in dataset_map:
        slug = path
        return html.Div(style={'display': 'flex'}, children=[
            html.Div(style={'width': '200px', 'padding': '20px', 'backgroundColor': '#f2f2f2'}, children=[
                html.H2("Dataset List"),
                html.Ul([
                    html.Li(html.A("🏠 Back to Home", href="/dash/")),
                    html.Li(html.A("🗺️ View Map", href=f"/dash/mapview?dataset={slug}")),
                    html.Hr(),
                    *[
                        html.Li(html.A(s, href=f"/dash/{s}")) for s in dataset_slugs
                    ]
                ])
            ]),
            html.Div(style={'flex': '1', 'padding': '20px'}, children=[
                generate_dataset_page(dataset_map[slug])
            ])
        ])
    else:
        return html.Div([
        html.H2("404 - Page not found"),
        html.P(f"No dataset or route found for: {pathname}")
    ])

def create_figure(dataset_url, log10=True, selected_sites=None):
    result = get_data(dataset_url, df["url_reference"], log10=log10)
    df_elt = result["elements"]
    df_data = result["data"]
    df_data['label'] = '<b>' + df_data['site_name'] + '</b>' + " - " + df_data['sample_name']

    # HTML-safe reference string
    refbib = html.A(df_data.at[0, 'reference'], href=df_data.at[0, 'url'], target='_blank')

    fig = go.Figure()

    for idx, row in df_elt.iterrows():
        site = df_data.loc[idx, 'site_name']
        if selected_sites and site not in selected_sites:
            continue

        label = df_data.loc[idx, 'label']
        customdata = [[label] for _ in df_elt.columns]

        fig.add_trace(go.Scatter(
            x=df_elt.columns,
            y=row.values,
            mode='lines+markers',
            customdata=customdata,
            hovertemplate='%{customdata[0]}<br><b>elt</b>: %{x} | <b>val</b>: %{y:.3f}<extra></extra>',
            name=label
        ))

    # dataset_name = re.search(r'[^/]+$', dataset_url).group()
    y_title = "Log10 Value" if log10 else "Original Value"

    fig.update_layout(
        # title=dict(
        #     text=f"Dataset: {dataset_name}",
        #     x=0,
        #     xanchor='left'
        # ),
        xaxis_title="Element",
        yaxis_title=y_title
    )

    # HTML layout for references
    ref_html = html.Div([
        html.H4("Sources & References"),
        html.Ul([
            html.Li([
                html.Span("API (data source): "),
                html.A(dataset_url, href=dataset_url, target='_blank')
            ]),
            html.Li([
                html.Span("Data reference: "),
                refbib
            ])
        ])
    ], style={'marginTop': '20px'})

    return fig, ref_html


def generate_dataset_page(dataset_url):
    dataset_name = re.search(r'[^/]+$', dataset_url).group()
    return html.Div(style={'display': 'flex', 'height': '100vh'}, children=[

        # Sidebar: Site Checklist
        html.Div(style={
            'width': '300px',
            'padding': '20px',
            'backgroundColor': '#e6e6e6',
            'overflowY': 'auto'
        }, children=[
            html.H3("Filter by Site"),

            html.Button("Select All", id='select-all-sites', n_clicks=0, style={'marginRight': '10px'}),
            html.Button("Unselect All", id='unselect-all-sites', n_clicks=0),

            html.Br(), html.Br(),

            dcc.Checklist(
                id='site-filter',
                options=[],   # Populated dynamically
                value=[],     # All selected by default
                labelStyle={'display': 'block'},
                inputStyle={'margin-right': '10px'}
            )
        ]),

        # Main Content: Graph and controls
        html.Div(style={'flex': '1', 'padding': '20px'}, children=[

            # Wrap titles + references in a horizontal row
            html.Div(style={'display': 'flex', 'justifyContent': 'space-between'}, children=[

                # Left column: Title and controls
                html.Div(style={'flex': '1', 'paddingRight': '20px'}, children=[
                    # html.H1(tit),
                    html.H2(f"Dataset: {dataset_name}", style={"marginBottom": "20px"}),
                    dcc.Store(id='current-dataset-url', data=dataset_url),
                    dcc.RadioItems(
                        id='scale-selector',
                        options=[
                            {'label': 'Log Scale', 'value': 'log'},
                            {'label': 'Linear Scale', 'value': 'linear'}
                        ],
                        value='log',
                        labelStyle={'display': 'inline-block', 'margin-right': '10px'}
                    ),
                ]),

                # Right column: Reference info
                html.Div(style={'flex': '2'}, children=[
                    html.Div(id='reference-info'),
                ])
            ]),

            # Graph goes below the 2-column block
            dcc.Graph(id='dataset-graph')
        ])
    ])

@app.callback(
    Output('dataset-graph', 'figure'),
    Output('reference-info', 'children'),
    Input('scale-selector', 'value'),
    Input('current-dataset-url', 'data'),
    Input('site-filter', 'value')
)
def update_graph(scale_mode, dataset_url, selected_sites):
    log10 = scale_mode == 'log'
    fig, ref_html = create_figure(dataset_url, log10=log10, selected_sites=selected_sites)
    return fig, ref_html

@app.callback(
    Output('site-filter', 'options'),
    Output('site-filter', 'value'),
    Input('current-dataset-url', 'data'),
    Input('select-all-sites', 'n_clicks'),
    Input('unselect-all-sites', 'n_clicks')#,
    # prevent_initial_call=True
)

def update_site_filter(dataset_url, select_clicks, unselect_clicks):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else 'current-dataset-url'

    result = get_data(dataset_url, df["url_reference"], log10=True)
    df_data = result["data"]
    site_names = sorted(df_data['site_name'].dropna().unique().tolist())
    options = [{'label': name, 'value': name} for name in site_names]

    if triggered_id in ('select-all-sites', 'current-dataset-url'):
        return options, site_names
    elif triggered_id == 'unselect-all-sites':
        return options, []
    else:
        raise dash.exceptions.PreventUpdate

# ----------- RUN SERVER ---------------- #

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
